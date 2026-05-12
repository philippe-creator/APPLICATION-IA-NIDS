"""
============================================================================
Module B — Security Engine | API FastAPI (main.py)
============================================================================
API REST pour le moteur de détection d'intrusions réseau (NIDS).

Endpoints :
  - POST /predict     : Analyse un flux réseau → verdict + SHAP
  - GET  /health      : État de santé de l'API
  - GET  /model-info  : Métadonnées des modèles chargés

L'API charge les modèles en mémoire au démarrage pour garantir
une latence d'inférence < 50ms (pattern Singleton).

Auteur  : Module B — Security Engine
Projet  : NIDS Cyber-IA (Cahier des Charges)
============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import os
import time
import numpy as np
import pandas as pd
import joblib
from functools import lru_cache
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from agent_ia import get_agent_response

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

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


# ══════════════════════════════════════════════════════════════════════════
# CHARGEMENT DES MODÈLES (Singleton — chargés une seule fois en RAM)
# ══════════════════════════════════════════════════════════════════════════

class ModelRegistry:
    """
    Registre centralisé des modèles ML chargés en mémoire.
    Pattern Singleton pour garantir un chargement unique et
    une latence d'inférence minimale.
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

    def _load_demo_mode(self):
        """
        Mode démonstration (si artefacts ML absents).
        Fournit une détection heuristique pour permettre de lancer l'app
        immédiatement et visualiser une réaction du moteur.
        """
        self.demo_mode = True
        self.is_loaded = True

        # Pas d'encodage spécifique requis dans ce mode
        self.label_encoders = {}
        self.scaler = None
        self.ae_scaler = None

        # Features attendues: on garde l'ordre de l'entrée API
        self.selected_features = [
            "dur","proto","service","state","spkts","dpkts","sbytes","dbytes","rate","sttl","dttl",
            "sload","dload","sloss","dloss","sinpkt","dinpkt","sjit","djit","swin","stcpb","dtcpb",
            "dwin","tcprtt","synack","ackdat","smean","dmean","trans_depth","response_body_len",
            "ct_srv_src","ct_state_ttl","ct_dst_ltm","ct_src_dport_ltm","ct_dst_sport_ltm",
            "ct_dst_src_ltm","is_ftp_login","ct_ftp_cmd","ct_flw_http_mthd","ct_src_ltm",
            "ct_srv_dst","is_sm_ips_ports",
        ]

        # Seuil d'anomalie "simple" (sur un score normalisé)
        self.ae_threshold = 0.85
        self.training_metrics = {
            "demo_mode": True,
            "note": "Artefacts ML absents. Heuristique activée (démo). Lancez train_model.py pour modèles réels.",
        }

        print("\n" + "=" * 60)
        print("  [DEMO MODE] Artefacts ML introuvables")
        print("  Pour entrainer les vrais modeles: python train_model.py")
        print("=" * 60)

    def load_all(self):
        """Charge tous les modèles et artefacts depuis le disque."""
        print("\n" + "=" * 60)
        print("  Chargement des modeles en memoire...")
        print("=" * 60)

        start = time.time()

        # Si les artefacts n'existent pas encore, activer un mode démonstration.
        required = [STACKING_MODEL_PATH, LABEL_ENCODERS_PATH, SCALER_PATH, SELECTED_FEATURES_PATH]
        if not all(os.path.exists(p) for p in required):
            self._load_demo_mode()
            return

        # Stacking Classifier
        self.stacking_model = joblib.load(STACKING_MODEL_PATH)
        print("  [OK] Stacking Classifier charge")

        # Auto-encodeur
        from tensorflow.keras.models import load_model
        self.autoencoder = load_model(AUTOENCODER_MODEL_PATH, compile=False)
        self.autoencoder.compile(optimizer="adam", loss="mse")
        print("  [OK] Auto-encodeur charge")

        # Seuil d'anomalie
        self.ae_threshold = joblib.load(AE_THRESHOLD_PATH)
        print(f"  [OK] Seuil d'anomalie : {self.ae_threshold:.6f}")

        # Scaler de l'auto-encodeur
        ae_scaler_path = AUTOENCODER_MODEL_PATH.replace(".keras", "_scaler.joblib")
        if os.path.exists(ae_scaler_path):
            self.ae_scaler = joblib.load(ae_scaler_path)
            print("  [OK] Scaler AE charge")

        # Label Encoders
        self.label_encoders = joblib.load(LABEL_ENCODERS_PATH)
        print(f"  [OK] Label Encoders charges ({len(self.label_encoders)} encodeurs)")

        # Standard Scaler
        self.scaler = joblib.load(SCALER_PATH)
        print("  [OK] StandardScaler charge")

        # Features sélectionnées
        self.selected_features = joblib.load(SELECTED_FEATURES_PATH)
        print(f"  [OK] Features selectionnees : {len(self.selected_features)}")

        # Métriques d'entraînement
        if os.path.exists(TRAINING_METRICS_PATH):
            self.training_metrics = joblib.load(TRAINING_METRICS_PATH)
            print("  [OK] Metriques d'entrainement chargees")

        # SHAP Explainer (TreeExplainer pour le stacking)
        # On utilise le premier estimateur (LightGBM) pour SHAP
        # car TreeExplainer est plus rapide que KernelExplainer
        if shap is not None:
            try:
                base_model = self.stacking_model.estimators_[0]  # LightGBM
                self.shap_explainer = shap.TreeExplainer(base_model)
                print("  [OK] SHAP TreeExplainer initialise (LightGBM)")
            except Exception as e:
                print(f"  [WARN] SHAP TreeExplainer echoue : {e}")
                self.shap_explainer = None
        else:
            print("  [WARN] SHAP non installe - explicabilite desactivee")
            self.shap_explainer = None

        elapsed = time.time() - start
        self.is_loaded = True
        print(f"\n  [OK] Tous les modeles charges en {elapsed:.2f}s")
        print("=" * 60)


# Instance globale du registre
registry = ModelRegistry()


# ══════════════════════════════════════════════════════════════════════════
# APPLICATION FASTAPI
# ══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Charge les modèles au démarrage de l'API."""
    registry.load_all()
    yield
    print("  Arrêt de l'API — libération des ressources.")


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════════════════
# FICHIERS STATIQUES ET PAGES WEB (Frontend)
# ══════════════════════════════════════════════════════════════════════════
app.mount("/static", StaticFiles(directory="static"), name="static")

def _get_html(filename: str) -> HTMLResponse:
    path = os.path.join("static", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content=f"<h1>Erreur 404</h1><p>Fichier {filename} introuvable.</p>", status_code=404)

@app.get("/", response_class=HTMLResponse, tags=["Web"])
async def root(): return _get_html("index.html")

@app.get("/home", response_class=HTMLResponse, tags=["Web"])
async def home_page(): return _get_html("home.html")

@app.get("/app", response_class=HTMLResponse, tags=["Web"])
async def app_page(): return _get_html("app.html")

@app.get("/dashboard", response_class=HTMLResponse, tags=["Web"])
async def dashboard_page(): return _get_html("dashboard.html")

# Historique global des événements en mémoire pour la démo
GLOBAL_EVENTS = []


# ══════════════════════════════════════════════════════════════════════════
# SCHÉMAS PYDANTIC (Entrée / Sortie)
# ══════════════════════════════════════════════════════════════════════════

class NetworkFlowInput(BaseModel):
    """
    Flux réseau en entrée pour l'analyse.
    Les champs correspondent aux features du dataset UNSW-NB15.
    """
    dur: float = Field(0.0, description="Durée de la transaction (secondes)")
    proto: str = Field("tcp", description="Protocole (tcp, udp, etc.)")
    service: str = Field("-", description="Service réseau (http, ftp, dns, etc.)")
    state: str = Field("FIN", description="État de la connexion")
    spkts: int = Field(0, description="Paquets source → destination")
    dpkts: int = Field(0, description="Paquets destination → source")
    sbytes: int = Field(0, description="Octets source → destination")
    dbytes: int = Field(0, description="Octets destination → source")
    rate: float = Field(0.0, description="Taux de paquets par seconde")
    sttl: int = Field(0, description="Time-to-live source")
    dttl: int = Field(0, description="Time-to-live destination")
    sload: float = Field(0.0, description="Charge source (bits/sec)")
    dload: float = Field(0.0, description="Charge destination (bits/sec)")
    sloss: int = Field(0, description="Paquets perdus (source)")
    dloss: int = Field(0, description="Paquets perdus (destination)")
    sinpkt: float = Field(0.0, description="Intervalle inter-paquets source")
    dinpkt: float = Field(0.0, description="Intervalle inter-paquets destination")
    sjit: float = Field(0.0, description="Jitter source")
    djit: float = Field(0.0, description="Jitter destination")
    swin: int = Field(0, description="Fenêtre TCP source")
    stcpb: int = Field(0, description="Numéro de séquence TCP source")
    dtcpb: int = Field(0, description="Numéro de séquence TCP destination")
    dwin: int = Field(0, description="Fenêtre TCP destination")
    tcprtt: float = Field(0.0, description="Round-trip time TCP")
    synack: float = Field(0.0, description="Temps SYN→SYN-ACK")
    ackdat: float = Field(0.0, description="Temps SYN-ACK→ACK")
    smean: int = Field(0, description="Taille moyenne des paquets source")
    dmean: int = Field(0, description="Taille moyenne des paquets destination")
    trans_depth: int = Field(0, description="Profondeur de la transaction HTTP")
    response_body_len: int = Field(0, description="Longueur du corps de la réponse")
    ct_srv_src: int = Field(0, description="Connexions de même service/source")
    ct_state_ttl: int = Field(0, description="Connexions de même état/TTL")
    ct_dst_ltm: int = Field(0, description="Connexions vers même destination")
    ct_src_dport_ltm: int = Field(0, description="Connexions source/port dest")
    ct_dst_sport_ltm: int = Field(0, description="Connexions dest/port source")
    ct_dst_src_ltm: int = Field(0, description="Connexions dest-source")
    is_ftp_login: int = Field(0, description="Login FTP (0/1)")
    ct_ftp_cmd: int = Field(0, description="Nombre de commandes FTP")
    ct_flw_http_mthd: int = Field(0, description="Nombre de méthodes HTTP")
    ct_src_ltm: int = Field(0, description="Connexions depuis la source")
    ct_srv_dst: int = Field(0, description="Connexions service/destination")
    is_sm_ips_ports: int = Field(0, description="IP/port identiques (0/1)")

    model_config = {"json_schema_extra": {
        "examples": [{
            "dur": 0.000011, "proto": "udp", "service": "-", "state": "INT",
            "spkts": 2, "dpkts": 0, "sbytes": 496, "dbytes": 0,
            "rate": 90909.09, "sttl": 254, "dttl": 0, "sload": 180363632.0,
            "dload": 0.0, "sloss": 0, "dloss": 0, "sinpkt": 0.011,
            "dinpkt": 0.0, "sjit": 0.0, "djit": 0.0, "swin": 0,
            "stcpb": 0, "dtcpb": 0, "dwin": 0, "tcprtt": 0.0,
            "synack": 0.0, "ackdat": 0.0, "smean": 248, "dmean": 0,
            "trans_depth": 0, "response_body_len": 0, "ct_srv_src": 2,
            "ct_state_ttl": 2, "ct_dst_ltm": 1, "ct_src_dport_ltm": 1,
            "ct_dst_sport_ltm": 1, "ct_dst_src_ltm": 2, "is_ftp_login": 0,
            "ct_ftp_cmd": 0, "ct_flw_http_mthd": 0, "ct_src_ltm": 1,
            "ct_srv_dst": 2, "is_sm_ips_ports": 0,
        }]
    }}


class PredictionResponse(BaseModel):
    """Réponse de l'API avec verdict, probabilité et explicabilité SHAP."""
    verdict: str = Field(..., description="ALLOW ou BLOCK")
    attack_probability: float = Field(..., description="Probabilité d'attaque [0-1]")
    is_anomaly: bool = Field(..., description="Détection d'anomalie (auto-encodeur)")
    anomaly_score: float = Field(..., description="Score d'erreur de reconstruction")
    anomaly_threshold: float = Field(..., description="Seuil d'anomalie configuré")
    shap_values: Dict[str, float] = Field(..., description="Valeurs SHAP par feature")
    top_features: List[str] = Field(..., description="Top 5 features explicatives")
    inference_time_ms: float = Field(..., description="Temps d'inférence (ms)")
    timestamp: str = Field(..., description="Horodatage de l'analyse")


class HealthResponse(BaseModel):
    """Réponse du health check."""
    status: str
    models_loaded: bool
    timestamp: str


class ModelInfoResponse(BaseModel):
    """Métadonnées des modèles."""
    selected_features: List[str]
    n_features: int
    anomaly_threshold: float
    anomaly_percentile: int
    stacking_metrics: Optional[Dict[str, Any]] = None
    autoencoder_metrics: Optional[Dict[str, Any]] = None


# ══════════════════════════════════════════════════════════════════════════
# LOGIQUE DE TRANSFORMATION ET PRÉDICTION
# ══════════════════════════════════════════════════════════════════════════

def transform_input(flow: NetworkFlowInput) -> pd.DataFrame:
    """
    Transforme un flux réseau JSON en DataFrame prêt pour l'inférence.
    Applique les mêmes transformations que le pipeline d'entraînement :
      1. Encodage des variables catégorielles
      2. Normalisation (StandardScaler)
      3. Sélection des features RFE

    Args:
        flow: Flux réseau (Pydantic model).

    Returns:
        pd.DataFrame: Ligne transformée prête pour la prédiction.
    """
    # Convertir en dict puis DataFrame
    data = flow.model_dump()
    df = pd.DataFrame([data])

    # Mode démo: pas de pipeline ML, on conserve les valeurs brutes
    if registry.demo_mode:
        for col in CATEGORICAL_COLUMNS:
            if col in df.columns:
                df[col] = 0  # placeholder numérique
        return df

    # Encoder les catégorielles
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns and col in registry.label_encoders:
            le = registry.label_encoders[col]
            val = df[col].iloc[0]
            if val in le.classes_:
                df[col] = le.transform(df[col])
            else:
                # Valeur inconnue → assigner la classe la plus fréquente (0)
                df[col] = 0

    # Normaliser
    df_scaled = pd.DataFrame(
        registry.scaler.transform(df),
        columns=df.columns
    )

    # Sélectionner les features RFE
    df_selected = df_scaled[registry.selected_features]

    return df_selected


def compute_shap_values(X: pd.DataFrame) -> Dict[str, float]:
    """
    Calcule les valeurs SHAP pour une prédiction.
    Utilise TreeExplainer (rapide) si disponible,
    sinon retourne des importances de base.

    Args:
        X: DataFrame d'une ligne avec les features sélectionnées.

    Returns:
        Dict[str, float]: Valeurs SHAP par feature.
    """
    if registry.shap_explainer is not None:
        try:
            shap_vals = registry.shap_explainer.shap_values(X)
            # Pour la classification binaire, prendre les SHAP de la classe 1
            if isinstance(shap_vals, list):
                vals = shap_vals[1][0]  # Classe "Attaque"
            else:
                vals = shap_vals[0]

            return {
                feat: round(float(val), 6)
                for feat, val in zip(registry.selected_features, vals)
            }
        except Exception:
            pass

    # Fallback : retourner des zéros
    return {feat: 0.0 for feat in registry.selected_features}

def _demo_predict(df_raw: pd.DataFrame) -> Dict[str, Any]:
    """
    Prédiction heuristique (démo).
    Utilise des signaux typiques DoS/scan: rate, sload, dur très faible, répétitions.
    """
    # valeurs manquantes -> 0
    r = float(df_raw.get("rate", 0.0).iloc[0] if "rate" in df_raw else 0.0)
    sload = float(df_raw.get("sload", 0.0).iloc[0] if "sload" in df_raw else 0.0)
    dur = float(df_raw.get("dur", 0.0).iloc[0] if "dur" in df_raw else 0.0)
    ct = float(df_raw.get("ct_dst_src_ltm", 0.0).iloc[0] if "ct_dst_src_ltm" in df_raw else 0.0)
    sbytes = float(df_raw.get("sbytes", 0.0).iloc[0] if "sbytes" in df_raw else 0.0)
    spkts = float(df_raw.get("spkts", 0.0).iloc[0] if "spkts" in df_raw else 0.0)

    # score brut (logit)
    logit = (
        0.00002 * r +
        0.0000005 * sload +
        0.15 * ct +
        0.0002 * sbytes +
        0.02 * spkts +
        (0.8 if dur < 0.002 and r > 5000 else 0.0)
    ) - 2.0

    proba = float(_sigmoid(logit))
    verdict = "BLOCK" if proba >= 0.70 else "ALLOW"

    # pseudo "anomaly score"
    anom = float(min(1.0, (r / 20000.0) + (sload / 5e7)))
    is_anomaly = anom >= float(registry.ae_threshold)

    shap = {
        "rate": round(0.00002 * r, 6),
        "sload": round(0.0000005 * sload, 6),
        "ct_dst_src_ltm": round(0.15 * ct, 6),
        "sbytes": round(0.0002 * sbytes, 6),
        "spkts": round(0.02 * spkts, 6),
        "dur": round(-0.4 if dur < 0.002 else 0.0, 6),
    }
    top = [k for k, _ in sorted(shap.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]]

    return {
        "verdict": verdict,
        "attack_probability": round(proba, 6),
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": round(anom, 6),
        "anomaly_threshold": round(float(registry.ae_threshold), 6),
        "shap_values": shap,
        "top_features": top,
    }


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

@app.post("/predict", response_model=PredictionResponse, tags=["Détection"])
async def predict(flow: NetworkFlowInput):
    """
    Analyse un flux reseau et renvoie un verdict de securite.

    Le moteur effectue deux analyses en parallèle :
    1. **Stacking Classifier** : détection des attaques connues
    2. **Auto-encodeur** : détection des anomalies zero-day

    La réponse inclut :
    - Le verdict (ALLOW / BLOCK)
    - La probabilité d'attaque
    - Le statut d'anomalie
    - Les valeurs SHAP pour l'explicabilité
    """
    if not registry.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Les modèles ne sont pas encore chargés."
        )

    start_time = time.time()

    try:
        # Transformer l'entrée
        X = transform_input(flow)

        # Mode démo: heuristique, pas de modèles
        if registry.demo_mode:
            demo = _demo_predict(X)
            inference_time = (time.time() - start_time) * 1000
            res = PredictionResponse(
                verdict=demo["verdict"],
                attack_probability=demo["attack_probability"],
                is_anomaly=demo["is_anomaly"],
                anomaly_score=demo["anomaly_score"],
                anomaly_threshold=demo["anomaly_threshold"],
                shap_values=demo["shap_values"],
                top_features=demo["top_features"],
                inference_time_ms=round(inference_time, 2),
                timestamp=datetime.now().isoformat(),
            )
            event_data = res.model_dump()
            GLOBAL_EVENTS.append(event_data)
            if len(GLOBAL_EVENTS) > 100:
                GLOBAL_EVENTS.pop(0)
            return res

        # 1. Stacking Classifier — Prédiction
        prediction = registry.stacking_model.predict(X)[0]
        proba = registry.stacking_model.predict_proba(X)[0]
        attack_probability = float(proba[1])

        # 2. Auto-encodeur — Détection d'anomalie
        X_ae = X.copy()
        if registry.ae_scaler is not None:
            X_ae = pd.DataFrame(
                registry.ae_scaler.transform(X_ae),
                columns=X_ae.columns
            )

        reconstructed = registry.autoencoder.predict(X_ae.values, verbose=0)
        anomaly_score = float(np.mean(np.power(X_ae.values - reconstructed, 2)))
        is_anomaly = anomaly_score > registry.ae_threshold

        # 3. Verdict final
        # BLOCK si le classifier dit "attaque" OU si l'auto-encodeur détecte une anomalie
        is_attack = prediction == 1 or is_anomaly
        verdict = "BLOCK" if is_attack else "ALLOW"

        # 4. SHAP — Explicabilité
        shap_vals = compute_shap_values(X)

        # Top 5 features les plus influentes (par valeur absolue)
        sorted_features = sorted(
            shap_vals.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        top_features = [f[0] for f in sorted_features[:5]]

        inference_time = (time.time() - start_time) * 1000  # en ms

        res = PredictionResponse(
            verdict=verdict,
            attack_probability=round(attack_probability, 6),
            is_anomaly=is_anomaly,
            anomaly_score=round(anomaly_score, 6),
            anomaly_threshold=round(registry.ae_threshold, 6),
            shap_values=shap_vals,
            top_features=top_features,
            inference_time_ms=round(inference_time, 2),
            timestamp=datetime.now().isoformat(),
        )
        event_data = res.model_dump()
        GLOBAL_EVENTS.append(event_data)
        if len(GLOBAL_EVENTS) > 100:
            GLOBAL_EVENTS.pop(0)
        return res

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'inférence : {str(e)}"
        )


@app.get("/health", response_model=HealthResponse, tags=["Système"])
async def health_check():
    """
    Verification de l'etat de sante de l'API.
    Retourne le statut de chargement des modèles.
    """
    return HealthResponse(
        status="healthy" if registry.is_loaded else "loading",
        models_loaded=registry.is_loaded,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/model-info", response_model=ModelInfoResponse, tags=["Système"])
async def model_info():
    """
    Metadonnees des modeles charges.
    Retourne les features sélectionnées, seuils, et métriques d'entraînement.
    """
    if not registry.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Les modèles ne sont pas encore chargés."
        )

    stacking_metrics = None
    ae_metrics = None

    if registry.training_metrics:
        sm = registry.training_metrics.get("stacking_classifier", {})
        stacking_metrics = {
            k: v for k, v in sm.items()
            if k != "confusion_matrix"  # Non sérialisable JSON
        }
        ae_metrics = registry.training_metrics.get("autoencoder", {})

    return ModelInfoResponse(
        selected_features=registry.selected_features,
        n_features=len(registry.selected_features),
        anomaly_threshold=round(registry.ae_threshold, 6),
        anomaly_percentile=AE_ANOMALY_PERCENTILE,
        stacking_metrics=stacking_metrics,
        autoencoder_metrics=ae_metrics,
    )


# ══════════════════════════════════════════════════════════════════════════
# UNIFIED APIs (Business logic & IA Agent)
# ══════════════════════════════════════════════════════════════════════════

class LoginReq(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login", tags=["Business"])
async def login(req: LoginReq):
    # Simulation de passage par le NIDS
    flow = NetworkFlowInput(dur=0.01, rate=10, sbytes=150)
    # Pour le login, on autorise admin/admin
    if req.username == "admin" and req.password == "admin":
        return {"access_token": "mock-jwt-token-12345", "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Identifiants incorrects")

@app.post("/api/business/deliveries", tags=["Business"])
async def create_delivery(req: Request):
    data = await req.json()
    # Mocking a normal flow for a delivery creation
    flow = NetworkFlowInput(dur=0.1, rate=50, sbytes=500, dbytes=300)
    sec_res = await predict(flow)
    if sec_res.verdict == "BLOCK":
        raise HTTPException(status_code=403, detail="Action bloquée par le NIDS")
    return {"status": "created", "security": sec_res.model_dump()}

@app.post("/api/business/stocks", tags=["Business"])
async def update_stock(req: Request):
    data = await req.json()
    # Mocking a flow
    flow = NetworkFlowInput(dur=0.05, rate=20, sbytes=200, dbytes=100)
    sec_res = await predict(flow)
    if sec_res.verdict == "BLOCK":
        raise HTTPException(status_code=403, detail="Action bloquée par le NIDS")
    return {"status": "updated", "security": sec_res.model_dump()}

@app.post("/api/business/external_monitor", tags=["Business"])
async def monitor_external(req: Request):
    data = await req.json()
    url = data.get("url", "")
    # Simulation d'un trafic atypique lié à une URL externe non vérifiée
    # Les URL suspectes (par ex, finissant par un domaine non reconnu) peuvent déclencher des flux plus lourds.
    if ".xyz" in url or "hacker" in url:
        flow = NetworkFlowInput(dur=0.001, rate=9000, sbytes=10000, dbytes=0) # Attack pattern
    else:
        flow = NetworkFlowInput(dur=0.2, rate=15, sbytes=600, dbytes=400) # Normal pattern

    sec_res = await predict(flow)
    if sec_res.verdict == "BLOCK":
        raise HTTPException(status_code=403, detail="Trafic vers URL externe bloqué par le NIDS")
    return {"status": "monitored", "url": url, "security": sec_res.model_dump()}

@app.get("/api/events", tags=["Dashboard"])
async def get_events():
    return GLOBAL_EVENTS[-50:]  # Return last 50 events

class AgentChatReq(BaseModel):
    message: str
    events: List[Dict[str, Any]]

@app.post("/api/agent/chat", tags=["Agent IA"])
async def agent_chat(req: AgentChatReq):
    response_text = get_agent_response(req.message, req.events)
    return {"response": response_text}


# ══════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
