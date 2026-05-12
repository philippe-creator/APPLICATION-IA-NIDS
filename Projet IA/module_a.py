"""
============================================================================
Module A — Interface Métier Logistique (Sidecar Client)
============================================================================
Expose des endpoints métier (ex: /deliveries, /stocks, /auth/login) et envoie
des métadonnées de flux au Module B (Security Engine) de manière asynchrone.

Objectif CdC:
- Découplage strict Module A / Module B (pattern Sidecar)
- Faible latence: traitement métier non bloquant par défaut
- Possibilité de mode bloquant pour transactions "à haut risque"
============================================================================
"""

from __future__ import annotations

import os
import time
import json
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

import httpx
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

# Import des modules de sécurité industrielle
from security_config import get_security_config, validate_environment
from industrial_middleware import (
    create_redis_client, IndustrialAuthenticator, 
    RateLimitMiddleware, SecurityAuditMiddleware, CircuitBreakerMiddleware,
    validate_industrial_input, require_auth
)
import redis
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration industrielle
config = get_security_config()
redis_client = create_redis_client()

# Validation environnement (mode démo si variables manquantes)
try:
    missing_vars = validate_environment()
    if missing_vars:
        print(f"⚠️ Variables d'environnement manquantes: {missing_vars}")
        print("🚀 Démarrage en mode démo...")
except Exception as e:
    print(f"⚠️ Erreur validation environnement: {e}")
    print("🚀 Démarrage en mode démo...")

# Configuration centrale
config = get_security_config()
MODULE_B_URL = os.getenv("MODULE_B_URL", "http://127.0.0.1:8000")
MODULE_B_PREDICT_ENDPOINT = os.getenv("MODULE_B_PREDICT_ENDPOINT", "/predict")

# Configuration JWT sécurisée
MODULE_A_JWT_SECRET = config["jwt"]["secret"]
MODULE_A_JWT_ALG = config["jwt"]["algorithm"]
JWT_EXPIRATION_MINUTES = config["jwt"]["expiration_minutes"]
JWT_REFRESH_EXPIRATION_DAYS = config["jwt"]["refresh_expiration_days"]

# Politique de décision industrielle
DEFAULT_BLOCKING_MODE = os.getenv("DEFAULT_BLOCKING_MODE", "false").lower() == "true"
BLOCK_THRESHOLD = float(os.getenv("BLOCK_THRESHOLD", "0.70"))

# Configuration Redis
redis_client = create_redis_client()
authenticator = IndustrialAuthenticator(redis_client)

# Logging structuré
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("module_a_industrial")


# ──────────────────────────────────────────────────────────────────────────
# Schémas
# ──────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must be alphanumeric')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class BusinessResponse(BaseModel):
    ok: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    security: Optional[Dict[str, Any]] = None
    blocking_mode: bool
    inference_time_ms: Optional[float] = None
    request_id: Optional[str] = None
    compliance_info: Optional[Dict[str, Any]] = None


class DeliveryCreate(BaseModel):
    delivery_id: str = Field(..., min_length=1, max_length=50)
    destination: str = Field(..., min_length=1, max_length=200)
    carrier: str = Field(..., min_length=1, max_length=100)
    priority: int = Field(1, ge=1, le=5)
    weight_kg: Optional[float] = Field(None, ge=0, le=10000)
    hazardous: bool = False
    temperature_controlled: bool = False
    
    @validator('delivery_id')
    def validate_delivery_id(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Delivery ID must be alphanumeric')
        return v


class StockUpdate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    delta: int = Field(..., ge=-10000, le=10000)
    warehouse: str = Field(..., min_length=1, max_length=100)
    reason: Optional[str] = Field(None, max_length=500)
    
    @validator('sku')
    def validate_sku(cls, v):
        if not v.replace('-', '_').isalnum():
            raise ValueError('SKU must be alphanumeric')
        return v


# ──────────────────────────────────────────────────────────────────────────
# JWT (auth simple pour la démo)
# ──────────────────────────────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)

def _issue_jwt(username: str, mfa_verified: bool = False) -> str:
    """Génère un token JWT avec configuration industrielle."""
    from jose import jwt
    now = int(time.time())
    payload = {
        "sub": username, 
        "iat": now, 
        "exp": now + (JWT_EXPIRATION_MINUTES * 60),
        "mfa_verified": mfa_verified,
        "scope": "industrial_access"
    }
    return jwt.encode(payload, MODULE_A_JWT_SECRET, algorithm=MODULE_A_JWT_ALG)


def _issue_refresh_token(username: str) -> str:
    """Génère un refresh token pour renouvellement automatique."""
    from jose import jwt
    now = int(time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + (JWT_REFRESH_EXPIRATION_DAYS * 24 * 60 * 60),
        "type": "refresh"
    }
    return jwt.encode(payload, MODULE_A_JWT_SECRET, algorithm=MODULE_A_JWT_ALG)


async def _require_auth_async(request: Request) -> str:
    """Authentification asynchrone avec logging."""
    try:
        payload = await authenticator.authenticate(request)
        logger.info(f"User {payload['sub']} authenticated successfully")
        return payload["sub"]
    except HTTPException as e:
        logger.warning(f"Authentication failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal authentication error"
        )


# ──────────────────────────────────────────────────────────────────────────
# Feature extraction "best effort"
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class FlowMeta:
    dur: float
    proto: str
    service: str
    state: str
    spkts: int
    dpkts: int
    sbytes: int
    dbytes: int
    rate: float
    sttl: int
    dttl: int
    sload: float
    dload: float
    sloss: int
    dloss: int
    sinpkt: float
    dinpkt: float
    sjit: float
    djit: float
    swin: int
    stcpb: int
    dtcpb: int
    dwin: int
    tcprtt: float
    synack: float
    ackdat: float
    smean: int
    dmean: int
    trans_depth: int
    response_body_len: int
    ct_srv_src: int
    ct_state_ttl: int
    ct_dst_ltm: int
    ct_src_dport_ltm: int
    ct_dst_sport_ltm: int
    ct_dst_src_ltm: int
    is_ftp_login: int
    ct_ftp_cmd: int
    ct_flw_http_mthd: int
    ct_src_ltm: int
    ct_srv_dst: int
    is_sm_ips_ports: int

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def _estimate_payload_size(payload: Any) -> int:
    try:
        return len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    except Exception:
        return 0


async def extract_flow_industrial(request: Request, start_ts: float, payload: Any) -> FlowMeta:
    """Extraction de flux avec contexte industriel et validation."""
    try:
        # Validation des seuils industriels
        flow_data = {
            "duration": max(0.0, time.time() - start_ts),
            "payload_size": _estimate_payload_size(payload),
            "connection_rate": 1.0  # Placeholder
        }
        
        # Validation industrielle
        validated_data = validate_industrial_input(flow_data)
        
        dur = validated_data["duration"]
        proto = "tcp"
        service = "http"
        state = "FIN"

        sbytes = validated_data["payload_size"]
        dbytes = 0
        spkts = max(1, int(sbytes / 600) + 1)
        dpkts = 0
        rate = spkts / dur if dur > 0 else float(spkts)

        # Logging pour audit
        logger.info(f"Flow extracted: duration={dur:.3f}s, bytes={sbytes}, rate={rate:.2f}")
        
        # Valeurs par défaut "neutres" avec contexte industriel
        return FlowMeta(
            dur=dur,
            proto=proto,
            service=service,
            state=state,
            spkts=spkts,
            dpkts=dpkts,
            sbytes=sbytes,
            dbytes=dbytes,
            rate=float(rate),
            sttl=254,
            dttl=0,
            sload=float(sbytes * 8 / dur) if dur > 0 else float(sbytes * 8),
            dload=0.0,
            sloss=0,
            dloss=0,
            sinpkt=dur / spkts if spkts > 0 else 0.0,
            dinpkt=0.0,
            sjit=0.0,
            djit=0.0,
            swin=0,
            stcpb=0,
            dtcpb=0,
            dwin=0,
            tcprtt=0.0,
        synack=0.0,
        ackdat=0.0,
        smean=int(sbytes / spkts) if spkts > 0 else 0,
        dmean=0,
        trans_depth=1,
        response_body_len=0,
        ct_srv_src=1,
        ct_state_ttl=1,
        ct_dst_ltm=1,
        ct_src_dport_ltm=1,
        ct_dst_sport_ltm=1,
        ct_dst_src_ltm=1,
        is_ftp_login=0,
        ct_ftp_cmd=0,
        ct_flw_http_mthd=1,
        ct_src_ltm=1,
        ct_srv_dst=1,
        is_sm_ips_ports=0,
    )
    except Exception as e:
        logger.error(f"Flow extraction error: {e}")
        # Fallback vers valeurs par défaut sécurisées
        return FlowMeta(
            dur=0.1, proto="tcp", service="http", state="FIN",
            spkts=1, dpkts=0, sbytes=100, dbytes=0, rate=10.0,
            sttl=254, dttl=0, sload=8000.0, dload=0.0,
            sloss=0, dloss=0, sinpkt=0.1, dinpkt=0.0,
            sjit=0.0, djit=0.0, swin=0, stcpb=0, dtcpb=0,
            dwin=0, tcprtt=0.0, synack=0.0, ackdat=0.0,
            smean=100, dmean=0, trans_depth=1, response_body_len=0,
            ct_srv_src=1, ct_state_ttl=1, ct_dst_ltm=1,
            ct_src_dport_ltm=1, ct_dst_sport_ltm=1, ct_dst_src_ltm=1,
            is_ftp_login=0, ct_ftp_cmd=0, ct_flw_http_mthd=1,
            ct_src_ltm=1, ct_srv_dst=1, is_sm_ips_ports=0,
        )


async def call_security_engine_industrial(flow: FlowMeta) -> Dict[str, Any]:
    """Appel au Security Engine avec retry et monitoring."""
    url = MODULE_B_URL.rstrip("/") + MODULE_B_PREDICT_ENDPOINT
    
    for attempt in range(3):  # Retry pattern
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=2.5) as client:
                r = await client.post(url, json=flow.to_dict())
                r.raise_for_status()
                response_time = time.time() - start_time
                
                # Monitoring de performance
                await redis_client.setex(
                    f"security_call:{int(time.time())}",
                    3600,
                    json.dumps({"response_time": response_time, "status": "success"})
                )
                
                logger.info(f"Security engine response: {response_time:.3f}s")
                return r.json()
                
        except httpx.TimeoutException:
            logger.warning(f"Security engine timeout (attempt {attempt + 1})")
            if attempt < 2:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            raise HTTPException(
                status_code=504,
                detail="Security engine unavailable"
            )
        except Exception as e:
            logger.error(f"Security engine error: {e}")
            if attempt < 2:
                continue
            raise


def call_security_engine_sync_industrial(flow_dict: Dict[str, Any]) -> None:
    """Best-effort fire-and-forget avec logging."""
    try:
        url = MODULE_B_URL.rstrip("/") + MODULE_B_PREDICT_ENDPOINT
        with httpx.Client(timeout=2.5) as client:
            response = client.post(url, json=flow_dict)
            logger.info(f"Async security call completed: {response.status_code}")
    except Exception as e:
        logger.warning(f"Async security call failed: {e}")
        return


async def analyze_request_industrial(request: Request, start_ts: float, payload: Any) -> Dict[str, Any]:
    """Analyse de requête avec contexte industriel."""
    try:
        flow = await extract_flow_industrial(request, start_ts, payload)
        return await call_security_engine_industrial(flow)
    except Exception as e:
        logger.error(f"Request analysis failed: {e}")
        # Fallback vers réponse sécurisée
        return {
            "verdict": "ALLOW",
            "attack_probability": 0.1,
            "is_anomaly": False,
            "error": "Analysis unavailable"
        }


# ──────────────────────────────────────────────────────────────────────────
# App FastAPI (Module A)
# ──────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Module A — Industrial Logistics API (NIDS)",
    version="2.0.0",
    description="Interface métier logistique industrielle avec sécurité NIDS intégrée.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration middleware industriel
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
app.add_middleware(SecurityAuditMiddleware, redis_client=redis_client)
app.add_middleware(CircuitBreakerMiddleware, redis_client=redis_client)

# CORS configuration sécurisée
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Dashboard uniquement
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "module_b_url": MODULE_B_URL}


@app.post("/auth/login", response_model=BusinessResponse)
async def login(payload: LoginRequest, request: Request):
    start_ts = time.time()

    # Démo: user/pass "admin/admin" sinon refus
    ok = payload.username == "admin" and payload.password == "admin"

    # Mode bloquant conseillé sur /auth/login
    blocking = True
    security_res: Optional[Dict[str, Any]] = None
    inference_ms: Optional[float] = None

    try:
        sec_start = time.time()
        security_res = await analyze_request(request, start_ts, payload.model_dump())
        inference_ms = (time.time() - sec_start) * 1000
    except Exception:
        # Ne pas casser l'app métier en cas d'indispo du module B
        security_res = {"verdict": "ALLOW", "attack_probability": 0.0, "is_anomaly": False}

    if security_res.get("attack_probability", 0.0) >= BLOCK_THRESHOLD or security_res.get("verdict") == "BLOCK":
        raise HTTPException(status_code=403, detail="Blocked by security engine")

    if not ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _issue_jwt(payload.username)
    return BusinessResponse(
        ok=True,
        data={"access_token": token, "token_type": "bearer"},
        security=security_res,
        blocking_mode=blocking,
        inference_time_ms=inference_ms,
    )


@app.post("/deliveries", response_model=BusinessResponse)
async def create_delivery(
    payload: DeliveryCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    creds: Optional[HTTPAuthorizationCredentials] = security,
):
    _require_auth(creds)
    start_ts = time.time()
    blocking = DEFAULT_BLOCKING_MODE or payload.priority >= 4

    security_res: Optional[Dict[str, Any]] = None
    inference_ms: Optional[float] = None

    if blocking:
        sec_start = time.time()
        try:
            security_res = await analyze_request(request, start_ts, payload.model_dump())
            inference_ms = (time.time() - sec_start) * 1000
        except Exception:
            security_res = {"verdict": "ALLOW", "attack_probability": 0.0, "is_anomaly": False}

        if security_res.get("attack_probability", 0.0) >= BLOCK_THRESHOLD or security_res.get("verdict") == "BLOCK":
            raise HTTPException(status_code=403, detail="Blocked by security engine")
    else:
        flow = await extract_flow(request, start_ts, payload.model_dump())
        background_tasks.add_task(call_security_engine_sync, flow.to_dict())

    return BusinessResponse(
        ok=True,
        data={"delivery_id": payload.delivery_id, "status": "created"},
        security=security_res,
        blocking_mode=blocking,
        inference_time_ms=inference_ms,
    )


@app.post("/stocks", response_model=BusinessResponse)
async def update_stock(payload: StockUpdate, request: Request, creds: Optional[HTTPAuthorizationCredentials] = security):
    _require_auth(creds)
    start_ts = time.time()
    blocking = DEFAULT_BLOCKING_MODE

    security_res: Optional[Dict[str, Any]] = None
    inference_ms: Optional[float] = None

    if blocking:
        sec_start = time.time()
        try:
            security_res = await analyze_request(request, start_ts, payload.model_dump())
            inference_ms = (time.time() - sec_start) * 1000
        except Exception:
            security_res = {"verdict": "ALLOW", "attack_probability": 0.0, "is_anomaly": False}

        if security_res.get("attack_probability", 0.0) >= BLOCK_THRESHOLD or security_res.get("verdict") == "BLOCK":
            raise HTTPException(status_code=403, detail="Blocked by security engine")

    return BusinessResponse(
        ok=True,
        data={"sku": payload.sku, "warehouse": payload.warehouse, "applied_delta": payload.delta},
        security=security_res,
        blocking_mode=blocking,
        inference_time_ms=inference_ms,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("module_a:app", host="0.0.0.0", port=int(os.getenv("MODULE_A_PORT", "9000")), reload=True)

