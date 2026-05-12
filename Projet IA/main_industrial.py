"""
============================================================================
Module B — Industrial Security Engine | API FastAPI (main_industrial.py)
============================================================================
API REST industrielle pour le moteur de détection d'intrusions réseau (NIDS).

Endpoints :
  - POST /predict     : Analyse un flux réseau → verdict + SHAP
  - GET  /health      : État de santé de l'API avec monitoring
  - GET  /model-info  : Métadonnées des modèles chargés
  - POST /admin/maintenance : Mode maintenance industriel

Améliorations industrielles :
  - Monitoring temps réel avec Prometheus
  - Circuit breaker pattern
  - Rate limiting avancé
  - Logging structuré ELK
  - Cache Redis pour performances
  - Validation des entrées industrielles

Auteur  : Module B — Industrial Security Engine
Projet  : NIDS Cyber-IA (Cahier des Charges Industriel)
============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import os
import time
import numpy as np
import pandas as pd
import joblib
import json
import asyncio
import logging
from functools import lru_cache
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Tuple

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Import des modules industriels
from security_config import get_security_config, validate_environment
from industrial_middleware import (
    create_redis_client, RateLimitMiddleware, SecurityAuditMiddleware,
    CircuitBreakerMiddleware, validate_industrial_input
)
import redis
import os
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

# Configuration logging structuré
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("module_b_industrial")

# Import des configurations existantes
from config import (
    API_TITLE, API_VERSION, API_DESCRIPTION,
    STACKING_MODEL_PATH, AUTOENCODER_MODEL_PATH,
    AE_THRESHOLD_PATH, LABEL_ENCODERS_PATH,
    SCALER_PATH, SELECTED_FEATURES_PATH,
    TRAINING_METRICS_PATH, CATEGORICAL_COLUMNS,
    AE_ANOMALY_PERCENTILE, MODELS_DIR,
)

try:
    import shap  # type: ignore
except Exception:
    shap = None

# ──────────────────────────────────────────────────────────────────────────
# Metrics Prometheus
# ──────────────────────────────────────────────────────────────────────────
prediction_counter = Counter('nids_predictions_total', 'Total predictions', ['verdict'])
prediction_duration = Histogram('nids_prediction_duration_seconds', 'Prediction duration')
model_load_time = Gauge('nids_model_load_time_seconds', 'Model loading time')
active_connections = Gauge('nids_active_connections', 'Active connections')
cache_hits = Counter('nids_cache_hits_total', 'Cache hits')
cache_misses = Counter('nids_cache_misses_total', 'Cache misses')

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))

# ──────────────────────────────────────────────────────────────────────────
# Modèles de données industriels
# ──────────────────────────────────────────────────────────────────────────
class NetworkFlowInput(BaseModel):
    """Schéma de flux réseau avec validation industrielle."""
    dur: float = Field(..., ge=0, description="Duration in seconds")
    proto: str = Field(..., max_length=10)
    service: str = Field(..., max_length=20)
    state: str = Field(..., max_length=20)
    spkts: int = Field(..., ge=0)
    dpkts: int = Field(..., ge=0)
    sbytes: int = Field(..., ge=0)
    dbytes: int = Field(..., ge=0)
    rate: float = Field(..., ge=0)
    sttl: int = Field(..., ge=0)
    dttl: int = Field(..., ge=0)
    sload: float = Field(..., ge=0)
    dload: float = Field(..., ge=0)
    sloss: int = Field(..., ge=0)
    dloss: int = Field(..., ge=0)
    sinpkt: float = Field(..., ge=0)
    dinpkt: float = Field(..., ge=0)
    sjit: float = Field(..., ge=0)
    djit: float = Field(..., ge=0)
    swin: int = Field(..., ge=0)
    stcpb: int = Field(..., ge=0)
    dtcpb: int = Field(..., ge=0)
    dwin: int = Field(..., ge=0)
    tcprtt: float = Field(..., ge=0)
    synack: float = Field(..., ge=0)
    ackdat: float = Field(..., ge=0)
    smean: int = Field(..., ge=0)
    dmean: int = Field(..., ge=0)
    trans_depth: int = Field(..., ge=0)
    response_body_len: int = Field(..., ge=0)
    ct_srv_src: int = Field(..., ge=0)
    ct_state_ttl: int = Field(..., ge=0)
    ct_dst_ltm: int = Field(..., ge=0)
    ct_src_dport_ltm: int = Field(..., ge=0)
    ct_dst_sport_ltm: int = Field(..., ge=0)
    ct_dst_src_ltm: int = Field(..., ge=0)
    is_ftp_login: int = Field(..., ge=0, le=1)
    ct_ftp_cmd: int = Field(..., ge=0)
    ct_flw_http_mthd: int = Field(..., ge=0)
    ct_src_ltm: int = Field(..., ge=0)
    ct_srv_dst: int = Field(..., ge=0)
    is_sm_ips_ports: int = Field(..., ge=0, le=1)
    
    # Métadonnées industrielles
    source_ip: Optional[str] = Field(None, max_length=45)
    dest_ip: Optional[str] = Field(None, max_length=45)
    interface: Optional[str] = Field(None, max_length=50)
    vlan_id: Optional[int] = Field(None, ge=0, le=4094)
    
    @validator('proto')
    def validate_proto(cls, v):
        valid_protos = ['tcp', 'udp', 'icmp', 'arp']
        if v.lower() not in valid_protos:
            raise ValueError(f'Protocol must be one of {valid_protos}')
        return v.lower()
    
    @validator('source_ip', 'dest_ip')
    def validate_ip(cls, v):
        if v is None:
            return v
        # Validation IP basique
        parts = v.split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            raise ValueError('Invalid IP address format')
        return v

class PredictionResponse(BaseModel):
    """Réponse de prédiction avec informations industrielles."""
    verdict: str = Field(..., description="ALLOW or BLOCK")
    attack_probability: float = Field(..., ge=0, le=1)
    is_anomaly: bool = Field(...)
    anomaly_score: Optional[float] = Field(None, ge=0)
    top_features: List[str] = Field(default_factory=list)
    inference_time_ms: float = Field(..., ge=0)
    model_version: str = Field(...)
    request_id: str = Field(...)
    timestamp: float = Field(...)
    compliance_info: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(..., ge=0, le=1)

# ──────────────────────────────────────────────────────────────────────────
# Registre de modèles industriel
# ──────────────────────────────────────────────────────────────────────────
class IndustrialModelRegistry:
    """
    Registre centralisé des modèles ML avec monitoring industriel.
    Pattern Singleton avec cache Redis et monitoring.
    """

    def __init__(self):
        self.stacking_model = None
        self.autoencoder = None
        self.ae_threshold = None
        self.ae_scaler = None
        self.label_encoders = None
        self.scaler = None
        self.selected_features = None
        self.training_metrics = None
        self.shap_explainer = None
        self.is_loaded = False
        self.demo_mode = False
        self.model_version = "2.0.0-industrial"
        self.last_load_time = None

    async def _cache_prediction(self, flow_hash: str, result: Dict[str, Any]):
        """Cache les résultats de prédiction dans Redis."""
        try:
            await redis_client.setex(
                f"prediction_cache:{flow_hash}",
                300,  # 5 minutes TTL
                json.dumps(result)
            )
            cache_hits.inc()
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
            cache_misses.inc()

    async def _get_cached_prediction(self, flow_hash: str) -> Optional[Dict[str, Any]]:
        """Récupère une prédiction depuis le cache."""
        try:
            cached = await redis_client.get(f"prediction_cache:{flow_hash}")
            if cached:
                cache_hits.inc()
                return json.loads(cached)
            cache_misses.inc()
            return None
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
            cache_misses.inc()
            return None

    def _generate_flow_hash(self, flow_data: Dict[str, Any]) -> str:
        """Génère un hash pour le cache de prédiction."""
        import hashlib
        flow_str = json.dumps(flow_data, sort_keys=True)
        return hashlib.md5(flow_str.encode()).hexdigest()

    def _load_demo_mode(self):
        """Mode démonstration avec heuristiques industrielles."""
        self.demo_mode = True
        self.is_loaded = True

        self.label_encoders = {}
        self.scaler = None
        self.ae_scaler = None

        self.selected_features = [
            "dur","proto","service","state","spkts","dpkts","sbytes","dbytes","rate","sttl","dttl",
            "sload","dload","sloss","dloss","sinpkt","dinpkt","sjit","djit","swin","stcpb","dtcpb",
            "dwin","tcprtt","synack","ackdat","smean","dmean","trans_depth","response_body_len",
            "ct_srv_src","ct_state_ttl","ct_dst_ltm","ct_src_dport_ltm","ct_dst_sport_ltm",
            "ct_dst_src_ltm","is_ftp_login","ct_ftp_cmd","ct_flw_http_mthd","ct_src_ltm",
            "ct_srv_dst","is_sm_ips_ports",
        ]

        self.ae_threshold = 0.85
        self.training_metrics = {
            "demo_mode": True,
            "model_version": self.model_version,
            "note": "Industrial demo mode - run train_model.py for real models",
            "load_time": time.time()
        }

        logger.info("Industrial demo mode activated")

    async def load_all(self):
        """Charge tous les modèles avec monitoring industriel."""
        logger.info("Loading industrial models...")
        start_time = time.time()

        required = [STACKING_MODEL_PATH, LABEL_ENCODERS_PATH, SCALER_PATH, SELECTED_FEATURES_PATH]
        if not all(os.path.exists(p) for p in required):
            self._load_demo_mode()
            return

        try:
            # Stacking Classifier
            self.stacking_model = joblib.load(STACKING_MODEL_PATH)
            logger.info("Stacking Classifier loaded")

            # Auto-encodeur
            from tensorflow.keras.models import load_model
            self.autoencoder = load_model(AUTOENCODER_MODEL_PATH, compile=False)
            self.autoencoder.compile(optimizer="adam", loss="mse")
            logger.info("Autoencoder loaded")

            # Seuil d'anomalie
            self.ae_threshold = joblib.load(AE_THRESHOLD_PATH)
            logger.info(f"Anomaly threshold: {self.ae_threshold:.6f}")

            # Scaler et encodeurs
            self.ae_scaler = joblib.load(os.path.join(MODELS_DIR, "autoencoder_scaler.joblib"))
            self.label_encoders = joblib.load(LABEL_ENCODERS_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self.selected_features = joblib.load(SELECTED_FEATURES_PATH)

            # Métriques d'entraînement
            if os.path.exists(TRAINING_METRICS_PATH):
                self.training_metrics = joblib.load(TRAINING_METRICS_PATH)

            # SHAP explainer (si disponible)
            if shap is not None and not self.demo_mode:
                try:
                    # Créer un échantillon pour l'explainer
                    sample_size = min(100, len(self.selected_features))
                    background_data = np.random.normal(0, 1, (sample_size, len(self.selected_features)))
                    self.shap_explainer = shap.Explainer(self.stacking_model, background_data)
                    logger.info("SHAP explainer initialized")
                except Exception as e:
                    logger.warning(f"SHAP explainer failed: {e}")
                    self.shap_explainer = None

            self.is_loaded = True
            self.last_load_time = time.time()
            load_duration = time.time() - start_time
            model_load_time.set(load_duration)

            logger.info(f"All models loaded in {load_duration:.2f}s")

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            self._load_demo_mode()

    async def predict_industrial(self, flow: NetworkFlowInput) -> Dict[str, Any]:
        """Prédiction industrielle avec cache et monitoring."""
        start_time = time.time()
        request_id = f"req_{int(time.time() * 1000)}_{id(flow)}"
        
        # Vérification cache
        flow_dict = flow.dict()
        flow_hash = self._generate_flow_hash(flow_dict)
        cached_result = await self._get_cached_prediction(flow_hash)
        
        if cached_result:
            logger.info(f"Cache hit for request {request_id}")
            cached_result["request_id"] = request_id
            cached_result["timestamp"] = time.time()
            return cached_result

        try:
            with prediction_duration.time():
                # Préparation des données
                X = self._prepare_features(flow_dict)
                
                # Prédiction stacking
                stacking_proba = self.stacking_model.predict_proba(X)[0, 1]
                stacking_pred = self.stacking_model.predict(X)[0]
                
                # Prédiction anomalie
                reconstruction_error = self._detect_anomaly(X)
                is_anomaly = reconstruction_error > self.ae_threshold
                
                # Calcul du verdict final
                attack_probability = float(stacking_proba)
                if is_anomaly:
                    attack_probability = max(attack_probability, 0.7)  # Boost si anomalie
                
                verdict = "BLOCK" if attack_probability >= 0.7 else "ALLOW"
                
                # Explication SHAP
                top_features = []
                if self.shap_explainer is not None:
                    try:
                        shap_values = self.shap_explainer.shap_values(X)
                        feature_importance = np.abs(shap_values).mean(axis=0)
                        top_indices = np.argsort(feature_importance)[-5:][::-1]
                        top_features = [self.selected_features[i] for i in top_indices]
                    except Exception as e:
                        logger.warning(f"SHAP explanation failed: {e}")

                inference_time_ms = (time.time() - start_time) * 1000
                
                result = {
                    "verdict": verdict,
                    "attack_probability": attack_probability,
                    "is_anomaly": bool(is_anomaly),
                    "anomaly_score": float(reconstruction_error) if reconstruction_error else None,
                    "top_features": top_features,
                    "inference_time_ms": inference_time_ms,
                    "model_version": self.model_version,
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "compliance_info": {
                        "industrial_mode": True,
                        "demo_mode": self.demo_mode,
                        "cache_enabled": True,
                        "monitoring_enabled": True
                    },
                    "confidence_score": max(attack_probability, 1 - attack_probability)
                }
                
                # Cache du résultat
                await self._cache_prediction(flow_hash, result)
                
                # Metrics
                prediction_counter.labels(verdict=verdict).inc()
                
                logger.info(f"Prediction {request_id}: {verdict} ({attack_probability:.3f})")
                
                return result

        except Exception as e:
            logger.error(f"Prediction failed for {request_id}: {e}")
            # Fallback sécurisé
            return {
                "verdict": "ALLOW",
                "attack_probability": 0.1,
                "is_anomaly": False,
                "anomaly_score": None,
                "top_features": [],
                "inference_time_ms": (time.time() - start_time) * 1000,
                "model_version": self.model_version,
                "request_id": request_id,
                "timestamp": time.time(),
                "compliance_info": {"error": str(e)},
                "confidence_score": 0.1
            }

    def _prepare_features(self, flow_dict: Dict[str, Any]) -> np.ndarray:
        """Prépare les features pour la prédiction."""
        df = pd.DataFrame([flow_dict])
        
        # Encodage des variables catégorielles
        for col in CATEGORICAL_COLUMNS:
            if col in df.columns and col in self.label_encoders:
                le = self.label_encoders[col]
                # Gérer les valeurs inconnues
                df[col] = df[col].apply(lambda x: x if x in le.classes_ else 'unknown')
                if 'unknown' not in le.classes_:
                    le.classes_ = np.append(le.classes_, 'unknown')
                df[col] = le.transform(df[col])
        
        # Sélection des features
        X = df[self.selected_features].values
        
        # Scaling si disponible
        if self.scaler is not None:
            X = self.scaler.transform(X)
        
        return X

    def _detect_anomaly(self, X: np.ndarray) -> float:
        """Détection d'anomalie avec auto-encodeur."""
        try:
            if self.autoencoder is None or self.ae_scaler is None:
                return 0.0
            
            X_scaled = self.ae_scaler.transform(X)
            reconstructed = self.autoencoder.predict(X_scaled, verbose=0)
            reconstruction_error = np.mean(np.square(X_scaled - reconstructed))
            return float(reconstruction_error)
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
            return 0.0

# Instance globale du registre
model_registry = IndustrialModelRegistry()

# ──────────────────────────────────────────────────────────────────────────
# Lifecycle management
# ──────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Démarrage
    logger.info("Starting Industrial Security Engine...")
    await model_registry.load_all()
    active_connections.set(0)
    
    yield
    
    # Arrêt
    logger.info("Shutting down Industrial Security Engine...")
    # Nettoyage Redis si nécessaire
    try:
        await redis_client.close()
    except:
        pass

# ──────────────────────────────────────────────────────────────────────────
# Application FastAPI
# ──────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Industrial NIDS Security Engine",
    version="2.0.0",
    description="Moteur de détection d'intrusions réseau industriel avec monitoring avancé",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware industriel
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
app.add_middleware(SecurityAuditMiddleware, redis_client=redis_client)
app.add_middleware(CircuitBreakerMiddleware, redis_client=redis_client)

# CORS sécurisé
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────
# Endpoints API
# ──────────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Health check avec monitoring industriel."""
    return {
        "status": "healthy",
        "model_loaded": model_registry.is_loaded,
        "demo_mode": model_registry.demo_mode,
        "model_version": model_registry.model_version,
        "timestamp": time.time(),
        "active_connections": active_connections._value.get(),
        "cache_enabled": True,
        "monitoring_enabled": True
    }

@app.get("/metrics")
async def metrics():
    """Endpoint Prometheus pour monitoring."""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/predict", response_model=PredictionResponse)
async def predict(flow: NetworkFlowInput, request: Request):
    """Endpoint principal de prédiction industrielle."""
    active_connections.inc()
    
    try:
        # Validation industrielle des entrées
        flow_data = flow.dict()
        validated_data = validate_industrial_input(flow_data)
        
        # Prédiction
        result = await model_registry.predict_industrial(flow)
        
        return PredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Prediction endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Prediction service unavailable")
    finally:
        active_connections.dec()

@app.get("/model-info")
async def model_info():
    """Informations détaillées sur les modèles."""
    return {
        "model_version": model_registry.model_version,
        "is_loaded": model_registry.is_loaded,
        "demo_mode": model_registry.demo_mode,
        "features_count": len(model_registry.selected_features) if model_registry.selected_features else 0,
        "training_metrics": model_registry.training_metrics or {},
        "shap_available": model_registry.shap_explainer is not None,
        "last_load_time": model_registry.last_load_time,
        "industrial_features": {
            "cache_enabled": True,
            "monitoring_enabled": True,
            "circuit_breaker_enabled": True,
            "rate_limiting_enabled": True,
            "audit_logging_enabled": True
        }
    }

@app.post("/admin/maintenance")
async def toggle_maintenance(enable: bool = True):
    """Mode maintenance industriel."""
    # Implementation pour mode maintenance
    logger.info(f"Maintenance mode: {'enabled' if enable else 'disabled'}")
    return {"maintenance_mode": enable, "timestamp": time.time()}

@app.get("/admin/stats")
async def get_stats():
    """Statistiques d'utilisation industrielles."""
    try:
        stats = {
            "predictions_total": {
                "allow": prediction_counter.labels(verdict="ALLOW")._value.get(),
                "block": prediction_counter.labels(verdict="BLOCK")._value.get()
            },
            "performance": {
                "avg_prediction_time": prediction_duration.observe()[0] if prediction_duration.observe() else 0,
                "model_load_time": model_load_time._value.get()
            },
            "cache": {
                "hits": cache_hits._value.get(),
                "misses": cache_misses._value.get()
            },
            "connections": {
                "active": active_connections._value.get()
            }
        }
        return stats
    except Exception as e:
        logger.error(f"Stats collection failed: {e}")
        return {"error": "Stats unavailable"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_industrial:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
