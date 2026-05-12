"""
============================================================================
Module B — Simple Security Engine | API FastAPI (Version Démo)
============================================================================
API REST simplifiée pour le moteur de détection d'intrusions réseau.
Version sans dépendances TensorFlow pour démarrage rapide.
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
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("module_b_simple")

# Configuration
API_TITLE = "NIDS Security Engine - Demo"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Moteur de détection d'intrusions réseau (mode démonstration)"

# Schémas de données
class NetworkFlowInput(BaseModel):
    """Schéma de flux réseau simplifié."""
    dur: float = Field(..., ge=0)
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
    
    source_ip: Optional[str] = Field(None, max_length=45)
    dest_ip: Optional[str] = Field(None, max_length=45)

class PredictionResponse(BaseModel):
    """Réponse de prédiction simplifiée."""
    verdict: str = Field(..., description="ALLOW or BLOCK")
    attack_probability: float = Field(..., ge=0, le=1)
    is_anomaly: bool = Field(...)
    anomaly_score: Optional[float] = Field(None, ge=0)
    top_features: List[str] = Field(default_factory=list)
    inference_time_ms: float = Field(..., ge=0)
    model_version: str = Field(...)
    request_id: str = Field(...)
    timestamp: float = Field(...)
    confidence_score: float = Field(..., ge=0, le=1)
    demo_mode: bool = True

# Modèle de démonstration
class SimpleModel:
    """Modèle de démonstration pour le NIDS."""
    
    def __init__(self):
        self.model_version = "1.0.0-demo"
        self.is_loaded = True
        self.demo_mode = True
        
        # Features importantes (exemple)
        self.important_features = [
            "sbytes", "rate", "spkts", "sttl", "dbytes", 
            "dpkts", "sload", "dload", "sjit", "djit"
        ]
        
        # Seuils de détection
        self.attack_threshold = 0.7
        self.anomaly_threshold = 0.8
        
    def predict(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prédiction de démonstration basée sur heuristiques simples."""
        start_time = time.time()
        
        # Heuristiques simples pour la démo
        attack_score = 0.0
        anomaly_score = 0.0
        
        # Vérifier les patterns suspects
        if flow_data.get("sbytes", 0) > 1000000:  # Gros upload
            attack_score += 0.3
            anomaly_score += 0.2
            
        if flow_data.get("rate", 0) > 10000:  # Taux élevé
            attack_score += 0.2
            anomaly_score += 0.3
            
        if flow_data.get("spkts", 0) > 10000:  # Beaucoup de paquets
            attack_score += 0.2
            anomaly_score += 0.1
            
        if flow_data.get("proto") == "icmp" and flow_data.get("spkts", 0) > 100:
            attack_score += 0.4  # ICMP flood possible
            
        # Ajouter un peu d'aléatoire pour la démo
        import random
        attack_score += random.uniform(0, 0.2)
        anomaly_score += random.uniform(0, 0.1)
        
        # Limiter les scores
        attack_score = min(attack_score, 1.0)
        anomaly_score = min(anomaly_score, 1.0)
        
        # Déterminer le verdict
        is_anomaly = anomaly_score > self.anomaly_threshold
        final_score = max(attack_score, anomaly_score if is_anomaly else 0)
        verdict = "BLOCK" if final_score >= self.attack_threshold else "ALLOW"
        
        # Générer un ID de requête
        request_id = f"req_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # Temps d'inférence
        inference_time = (time.time() - start_time) * 1000
        
        # Features importantes pour cette prédiction
        top_features = []
        if flow_data.get("sbytes", 0) > 500000:
            top_features.append("sbytes")
        if flow_data.get("rate", 0) > 5000:
            top_features.append("rate")
        if flow_data.get("spkts", 0) > 5000:
            top_features.append("spkts")
            
        return {
            "verdict": verdict,
            "attack_probability": final_score,
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score if is_anomaly else None,
            "top_features": top_features[:3],
            "inference_time_ms": inference_time,
            "model_version": self.model_version,
            "request_id": request_id,
            "timestamp": time.time(),
            "confidence_score": max(final_score, 1 - final_score),
            "demo_mode": True
        }

# Instance du modèle
model = SimpleModel()

# Application FastAPI
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
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

@app.get("/")
async def root():
    """Endpoint racine."""
    return {
        "message": "NIDS Security Engine - Demo Mode",
        "version": API_VERSION,
        "status": "running",
        "model_loaded": model.is_loaded,
        "demo_mode": model.demo_mode
    }

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "model_loaded": model.is_loaded,
        "demo_mode": model.demo_mode,
        "model_version": model.model_version,
        "timestamp": time.time()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(flow: NetworkFlowInput, request: Request):
    """Endpoint principal de prédiction."""
    try:
        # Convertir en dictionnaire
        flow_data = flow.dict()
        
        # Faire la prédiction
        result = model.predict(flow_data)
        
        # Logger la prédiction
        logger.info(f"Prediction {result['request_id']}: {result['verdict']} ({result['attack_probability']:.3f})")
        
        return PredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Prediction service unavailable"
        )

@app.get("/model-info")
async def model_info():
    """Informations sur le modèle."""
    return {
        "model_version": model.model_version,
        "is_loaded": model.is_loaded,
        "demo_mode": model.demo_mode,
        "features_count": len(model.important_features),
        "important_features": model.important_features,
        "attack_threshold": model.attack_threshold,
        "anomaly_threshold": model.anomaly_threshold,
        "model_type": "Heuristic-based Demo Model",
        "description": "Modèle de démonstration pour tests du NIDS"
    }

@app.get("/admin/stats")
async def get_stats():
    """Statistiques de démonstration."""
    return {
        "predictions_total": {
            "allow": 75,
            "block": 25
        },
        "performance": {
            "avg_prediction_time": 0.015,
            "model_load_time": 0.001
        },
        "cache": {
            "hits": 0,
            "misses": 0
        },
        "connections": {
            "active": 1
        },
        "demo_mode": True
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  NIDS SECURITY ENGINE - DEMO MODE")
    print("="*60)
    print("  • Mode: Démonstration (heuristiques simples)")
    print("  • Modèle: Basé sur règles et heuristiques")
    print("  • Objectif: Tests d'intégration et démonstration")
    print("="*60)
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
