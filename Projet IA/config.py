"""
============================================================================
Module B — Security Engine | Configuration Centralisée
============================================================================
Fichier de configuration pour le pipeline NIDS Cyber-IA.
Regroupe tous les chemins, hyperparamètres et constantes partagés.
============================================================================
"""

import os

# ──────────────────────────────────────────────────────────────────────────
# Chemins
# ──────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE_DIR  # Les CSV sont à la racine du projet
MODELS_DIR = os.path.join(BASE_DIR, "models")

TRAIN_CSV = os.path.join(DATA_DIR, "UNSW_NB15_training-set.csv")
TEST_CSV = os.path.join(DATA_DIR, "UNSW_NB15_testing-set.csv")

# Créer le dossier models s'il n'existe pas
os.makedirs(MODELS_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────
# Colonnes
# ──────────────────────────────────────────────────────────────────────────
# Colonnes à supprimer avant l'entraînement (id technique + catégorie texte)
COLUMNS_TO_DROP = ["id", "attack_cat"]

# Colonnes catégorielles à encoder
CATEGORICAL_COLUMNS = ["proto", "service", "state"]

# Variable cible (binaire : 0 = Normal, 1 = Attaque)
TARGET_COLUMN = "label"

# ──────────────────────────────────────────────────────────────────────────
# Prétraitement
# ──────────────────────────────────────────────────────────────────────────
# RFE : nombre de features à sélectionner (CdC : 15-20, couvrant ≥ 95%)
RFE_N_FEATURES = 20

# SMOTE : stratégie de suréchantillonnage
SMOTE_RANDOM_STATE = 42
SMOTE_K_NEIGHBORS = 5

# Scaler
SCALER_TYPE = "standard"  # "standard" ou "minmax"

# ──────────────────────────────────────────────────────────────────────────
# Modèles — Stacking Classifier
# ──────────────────────────────────────────────────────────────────────────
RANDOM_STATE = 42

# LightGBM
LGBM_PARAMS = {
    "n_estimators": 200,
    "learning_rate": 0.05,
    "max_depth": 7,
    "num_leaves": 63,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": RANDOM_STATE,
    "verbose": -1,
    "n_jobs": -1,
}

# XGBoost
XGB_PARAMS = {
    "n_estimators": 200,
    "learning_rate": 0.05,
    "max_depth": 7,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "random_state": RANDOM_STATE,
    "use_label_encoder": False,
    "eval_metric": "logloss",
    "n_jobs": -1,
}

# Random Forest
RF_PARAMS = {
    "n_estimators": 300,
    "max_depth": 15,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
}

# Méta-classifieur (Logistic Regression)
META_CLF_PARAMS = {
    "C": 1.0,
    "max_iter": 1000,
    "random_state": RANDOM_STATE,
}

# ──────────────────────────────────────────────────────────────────────────
# Auto-encodeur (Denoising Autoencoder)
# ──────────────────────────────────────────────────────────────────────────
AE_NOISE_FACTOR = 0.1          # Intensité du bruit gaussien
AE_ENCODING_DIM = 16           # Dimension du goulot d'étranglement (bottleneck)
AE_HIDDEN_DIM = 64             # Dimension des couches cachées
AE_EPOCHS = 50                 # Nombre d'époques d'entraînement
AE_BATCH_SIZE = 256            # Taille du batch
AE_VALIDATION_SPLIT = 0.1     # Part de validation
AE_ANOMALY_PERCENTILE = 95    # Centile pour le seuil d'anomalie

# ──────────────────────────────────────────────────────────────────────────
# API FastAPI
# ──────────────────────────────────────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000
API_TITLE = "NIDS Cyber-IA — Security Engine API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
Module B du système NIDS Cyber-IA.
Moteur de détection d'intrusions réseau basé sur le Machine Learning.
Reçoit un flux JSON de métadonnées réseau et renvoie un verdict de sécurité
avec explicabilité SHAP.
"""

# ──────────────────────────────────────────────────────────────────────────
# Fichiers de modèles sauvegardés
# ──────────────────────────────────────────────────────────────────────────
STACKING_MODEL_PATH = os.path.join(MODELS_DIR, "stacking_classifier.joblib")
AUTOENCODER_MODEL_PATH = os.path.join(MODELS_DIR, "autoencoder.keras")
AE_THRESHOLD_PATH = os.path.join(MODELS_DIR, "autoencoder_threshold.joblib")
LABEL_ENCODERS_PATH = os.path.join(MODELS_DIR, "label_encoders.joblib")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.joblib")
RFE_SELECTOR_PATH = os.path.join(MODELS_DIR, "rfe_selector.joblib")
SELECTED_FEATURES_PATH = os.path.join(MODELS_DIR, "selected_features.joblib")
TRAINING_METRICS_PATH = os.path.join(MODELS_DIR, "training_metrics.joblib")
