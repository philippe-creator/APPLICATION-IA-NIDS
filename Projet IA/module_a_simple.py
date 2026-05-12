"""
============================================================================
Module A — Simple Logistics API (Demo Version)
============================================================================
API métier simplifiée sans dépendances Redis pour démonstration rapide.
============================================================================
"""

from __future__ import annotations

import os
import time
import json
import asyncio
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("module_a_simple")

# Configuration
MODULE_B_URL = os.getenv("MODULE_B_URL", "http://localhost:8000")
MODULE_B_PREDICT_ENDPOINT = "/predict"

# Schémas de données
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

class BusinessResponse(BaseModel):
    ok: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    security: Optional[Dict[str, Any]] = None
    blocking_mode: bool = False
    inference_time_ms: Optional[float] = None
    request_id: Optional[str] = None

class DeliveryCreate(BaseModel):
    delivery_id: str = Field(..., min_length=1, max_length=50)
    destination: str = Field(..., min_length=1, max_length=200)
    carrier: str = Field(..., min_length=1, max_length=100)
    priority: int = Field(1, ge=1, le=5)
    weight_kg: Optional[float] = Field(None, ge=0, le=10000)
    hazardous: bool = False
    temperature_controlled: bool = False

class StockUpdate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    delta: int = Field(..., ge=-10000, le=10000)
    warehouse: str = Field(..., min_length=1, max_length=100)
    reason: Optional[str] = Field(None, max_length=500)

# Application FastAPI
app = FastAPI(
    title="Module A — Simple Logistics API",
    version="1.0.0-demo",
    description="API métier logistique simplifiée pour démonstration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT simple pour la démo
def _generate_simple_token(username: str) -> str:
    """Génère un token JWT simple pour la démo."""
    import base64
    import hashlib
    payload = f"{username}:{int(time.time())}"
    return base64.b64encode(payload.encode()).decode()

def _verify_simple_token(token: str) -> Optional[str]:
    """Vérifie un token simple."""
    try:
        import base64
        decoded = base64.b64decode(token.encode()).decode()
        username, timestamp = decoded.split(":")
        # Token valide pour 1 heure
        if int(time.time()) - int(timestamp) < 3600:
            return username
    except:
        pass
    return None

async def call_security_engine(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Appelle le Module B pour analyse de sécurité."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MODULE_B_URL}{MODULE_B_PREDICT_ENDPOINT}",
                json=flow_data
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Security engine call failed: {e}")
        # Fallback si Module B indisponible
        return {
            "verdict": "ALLOW",
            "attack_probability": 0.1,
            "is_anomaly": False,
            "inference_time_ms": 0.0,
            "request_id": f"fallback_{int(time.time())}",
            "demo_mode": True
        }

def extract_flow_metadata(request: Request, payload: Any) -> Dict[str, Any]:
    """Extrait les métadonnées de flux de la requête."""
    return {
        "dur": 0.1,  # Placeholder
        "proto": "tcp",
        "service": "http",
        "state": "FIN",
        "spkts": 10,
        "dpkts": 8,
        "sbytes": len(json.dumps(payload).encode()) if payload else 100,
        "dbytes": 50,
        "rate": 100.0,
        "sttl": 64,
        "dttl": 64,
        "sload": 800.0,
        "dload": 400.0,
        "sloss": 0,
        "dloss": 0,
        "sinpkt": 0.01,
        "dinpkt": 0.0125,
        "sjit": 0.0,
        "djit": 0.0,
        "swin": 0,
        "stcpb": 0,
        "dtcpb": 0,
        "dwin": 0,
        "tcprtt": 0.0,
        "synack": 0.0,
        "ackdat": 0.0,
        "smean": 10,
        "dmean": 6,
        "trans_depth": 1,
        "response_body_len": 0,
        "ct_srv_src": 1,
        "ct_state_ttl": 1,
        "ct_dst_ltm": 1,
        "ct_src_dport_ltm": 1,
        "ct_dst_sport_ltm": 1,
        "ct_dst_src_ltm": 1,
        "is_ftp_login": 0,
        "ct_ftp_cmd": 0,
        "ct_flw_http_mthd": 1,
        "ct_src_ltm": 1,
        "ct_srv_dst": 1,
        "is_sm_ips_ports": 0,
        "source_ip": request.client.host if request.client else "unknown",
        "dest_ip": "127.0.0.1"
    }

# Endpoints
@app.get("/")
async def root():
    """Endpoint racine."""
    return {
        "message": "Module A - Simple Logistics API",
        "version": "1.0.0-demo",
        "status": "running",
        "module_b_url": MODULE_B_URL
    }

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "module_b_url": MODULE_B_URL,
        "demo_mode": True
    }

@app.post("/auth/login", response_model=BusinessResponse)
async def login(payload: LoginRequest, request: Request):
    """Authentification simplifiée."""
    start_ts = time.time()
    
    # Extraction des métadonnées
    flow_data = extract_flow_metadata(request, payload.dict())
    
    # Appel au moteur de sécurité
    security_result = await call_security_engine(flow_data)
    
    # Simulation d'authentification
    success = payload.username == "admin" and payload.password == "admin123"
    
    if success:
        token = _generate_simple_token(payload.username)
        return BusinessResponse(
            ok=True,
            data={"token": token, "user": payload.username},
            security=security_result,
            blocking_mode=security_result.get("verdict") == "BLOCK",
            inference_time_ms=security_result.get("inference_time_ms"),
            request_id=security_result.get("request_id")
        )
    else:
        return BusinessResponse(
            ok=False,
            data={"error": "Invalid credentials"},
            security=security_result,
            blocking_mode=False
        )

@app.post("/deliveries", response_model=BusinessResponse)
async def create_delivery(payload: DeliveryCreate, request: Request):
    """Création de livraison."""
    start_ts = time.time()
    
    # Extraction des métadonnées
    flow_data = extract_flow_metadata(request, payload.dict())
    
    # Appel au moteur de sécurité
    security_result = await call_security_engine(flow_data)
    
    # Simulation de création
    delivery_data = {
        "delivery_id": payload.delivery_id,
        "status": "created",
        "created_at": time.time(),
        "priority": payload.priority
    }
    
    return BusinessResponse(
        ok=True,
        data=delivery_data,
        security=security_result,
        blocking_mode=security_result.get("verdict") == "BLOCK",
        inference_time_ms=security_result.get("inference_time_ms"),
        request_id=security_result.get("request_id")
    )

@app.put("/stocks/{sku}", response_model=BusinessResponse)
async def update_stock(sku: str, payload: StockUpdate, request: Request):
    """Mise à jour de stock."""
    start_ts = time.time()
    
    # Extraction des métadonnées
    flow_data = extract_flow_metadata(request, {"sku": sku, **payload.dict()})
    
    # Appel au moteur de sécurité
    security_result = await call_security_engine(flow_data)
    
    # Simulation de mise à jour
    stock_data = {
        "sku": sku,
        "delta": payload.delta,
        "warehouse": payload.warehouse,
        "updated_at": time.time(),
        "new_stock": 1000 + payload.delta  # Simulation
    }
    
    return BusinessResponse(
        ok=True,
        data=stock_data,
        security=security_result,
        blocking_mode=security_result.get("verdict") == "BLOCK",
        inference_time_ms=security_result.get("inference_time_ms"),
        request_id=security_result.get("request_id")
    )

@app.get("/deliveries")
async def list_deliveries():
    """Liste des livraisons (simulation)."""
    return {
        "deliveries": [
            {
                "delivery_id": "DEL001",
                "status": "in_transit",
                "destination": "Paris",
                "carrier": "DHL",
                "priority": 1
            },
            {
                "delivery_id": "DEL002", 
                "status": "delivered",
                "destination": "Lyon",
                "carrier": "FedEx",
                "priority": 2
            }
        ]
    }

@app.get("/stocks")
async def list_stocks():
    """Liste des stocks (simulation)."""
    return {
        "stocks": [
            {"sku": "PROD001", "quantity": 1500, "warehouse": "WH1"},
            {"sku": "PROD002", "quantity": 800, "warehouse": "WH1"},
            {"sku": "PROD003", "quantity": 2200, "warehouse": "WH2"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  MODULE A - SIMPLE LOGISTICS API")
    print("="*60)
    print("  • Mode: Démonstration")
    print("  • Auth: admin/admin123")
    print("  • Module B:", MODULE_B_URL)
    print("="*60)
    
    uvicorn.run(
        "module_a_simple:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        log_level="info"
    )
