"""
============================================================================
Module B — Security Engine | Entraînement des Modèles (train_model.py)
============================================================================
Ce script entraîne les deux moteurs de détection du NIDS :

  1. Stacking Classifier (attaques connues)
     - Base Learners : LightGBM, XGBoost, Random Forest
     - Méta-classifieur : Logistic Regression
     - Objectif : Accuracy > 98%, F1-Score élevé

  2. Auto-encodeur Débruité (attaques zero-day)
     - Entraîné exclusivement sur le trafic normal
     - Seuil d'anomalie au 95ème centile
     - Architecture : Input → Noise → 64 → 16 → 64 → Output

Auteur  : Module B — Security Engine
Projet  : NIDS Cyber-IA (Cahier des Charges)
============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import time

# Sklearn
from sklearn.ensemble import (
    StackingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# Gradient Boosting
import xgboost as xgb
import lightgbm as lgb

# Deep Learning (Auto-encodeur)
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model

# Configuration
from config import (
    LGBM_PARAMS, XGB_PARAMS, RF_PARAMS, META_CLF_PARAMS,
    AE_NOISE_FACTOR, AE_ENCODING_DIM, AE_HIDDEN_DIM,
    AE_EPOCHS, AE_BATCH_SIZE, AE_VALIDATION_SPLIT,
    AE_ANOMALY_PERCENTILE, RANDOM_STATE,
    STACKING_MODEL_PATH, AUTOENCODER_MODEL_PATH,
    AE_THRESHOLD_PATH, TRAINING_METRICS_PATH,
)

# Prétraitement
from preprocess import run_preprocessing


# ══════════════════════════════════════════════════════════════════════════
# 1. STACKING CLASSIFIER
# ══════════════════════════════════════════════════════════════════════════

def build_stacking_classifier():
    """
    Construit le Stacking Classifier hybride avec :
      - LightGBM
      - XGBoost
      - Random Forest
      - Logistic Regression (méta-classifieur)

    Returns:
        StackingClassifier: Modèle non entraîné.
    """
    print("\n" + "=" * 70)
    print("  CONSTRUCTION DU STACKING CLASSIFIER")
    print("=" * 70)

    # Base learners
    lgbm_clf = lgb.LGBMClassifier(**LGBM_PARAMS)
    xgb_clf = xgb.XGBClassifier(**XGB_PARAMS)
    rf_clf = RandomForestClassifier(**RF_PARAMS)

    # Méta-classifieur
    meta_clf = LogisticRegression(**META_CLF_PARAMS)

    # Stacking
    stacking = StackingClassifier(
        estimators=[
            ("lightgbm", lgbm_clf),
            ("xgboost", xgb_clf),
            ("random_forest", rf_clf),
        ],
        final_estimator=meta_clf,
        cv=5,
        stack_method="predict_proba",
        n_jobs=-1,
        verbose=1,
    )

    print("  ✓ Base Learners :")
    print("      1. LightGBM   (n_estimators=200, max_depth=7)")
    print("      2. XGBoost    (n_estimators=200, max_depth=7)")
    print("      3. Random Forest (n_estimators=300, max_depth=15)")
    print("  ✓ Méta-classifieur : Logistic Regression (C=1.0)")
    print("  ✓ Cross-validation : 5-fold")

    return stacking


def train_stacking(X_train, y_train, X_test, y_test):
    """
    Entraîne le Stacking Classifier et évalue ses performances.

    Args:
        X_train: Features d'entraînement (après SMOTE + RFE).
        y_train: Labels d'entraînement.
        X_test: Features de test (après RFE).
        y_test: Labels de test.

    Returns:
        tuple: (model, metrics_dict)
    """
    model = build_stacking_classifier()

    print("\n" + "=" * 70)
    print("  ENTRAÎNEMENT DU STACKING CLASSIFIER")
    print("=" * 70)
    print(f"  → Train set : {X_train.shape[0]:,} échantillons × {X_train.shape[1]} features")
    print(f"  → Test set  : {X_test.shape[0]:,} échantillons × {X_test.shape[1]} features")
    print("  → Entraînement en cours (cela peut prendre quelques minutes)...\n")

    start_time = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_time

    print(f"\n  ✓ Entraînement terminé en {train_time:.1f}s")

    # ── Évaluation ──
    print("\n" + "=" * 70)
    print("  ÉVALUATION DU STACKING CLASSIFIER")
    print("=" * 70)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted")
    rec = recall_score(y_test, y_pred, average="weighted")
    f1 = f1_score(y_test, y_pred, average="weighted")

    print(f"\n  ┌─────────────────────────────────┐")
    print(f"  │   MÉTRIQUES DE PERFORMANCE      │")
    print(f"  ├─────────────────────────────────┤")
    print(f"  │  Accuracy  : {acc:.4f}            │")
    print(f"  │  Precision : {prec:.4f}            │")
    print(f"  │  Recall    : {rec:.4f}            │")
    print(f"  │  F1-Score  : {f1:.4f}            │")
    print(f"  └─────────────────────────────────┘")

    print(f"\n  Classification Report :\n")
    report = classification_report(
        y_test, y_pred,
        target_names=["Normal (0)", "Attaque (1)"]
    )
    print(report)

    print(f"  Matrice de Confusion :")
    cm = confusion_matrix(y_test, y_pred)
    print(f"                    Prédit Normal  Prédit Attaque")
    print(f"  Réel Normal       {cm[0][0]:>10,}    {cm[0][1]:>10,}")
    print(f"  Réel Attaque      {cm[1][0]:>10,}    {cm[1][1]:>10,}")

    # Sauvegarder le modèle
    joblib.dump(model, STACKING_MODEL_PATH)
    print(f"\n  ✓ Modèle sauvegardé → {STACKING_MODEL_PATH}")

    metrics = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm,
        "training_time_seconds": train_time,
    }

    return model, metrics


# ══════════════════════════════════════════════════════════════════════════
# 2. AUTO-ENCODEUR DÉBRUITÉ (Denoising Autoencoder)
# ══════════════════════════════════════════════════════════════════════════

def build_autoencoder(input_dim):
    """
    Construit un Auto-encodeur Débruité (DAE) pour la détection
    d'anomalies zero-day.

    Architecture (conforme au CdC) :
        Input → GaussianNoise(0.1) → Dense(64, relu) → Dense(16, relu)
              → Dense(64, relu) → Dense(input_dim, sigmoid)

    Args:
        input_dim: Nombre de features en entrée.

    Returns:
        keras.Model: Auto-encodeur compilé.
    """
    print("\n" + "=" * 70)
    print("  CONSTRUCTION DE L'AUTO-ENCODEUR DÉBRUITÉ (DAE)")
    print("=" * 70)

    # Encodeur
    inputs = layers.Input(shape=(input_dim,), name="encoder_input")
    x = layers.GaussianNoise(AE_NOISE_FACTOR, name="gaussian_noise")(inputs)
    x = layers.Dense(AE_HIDDEN_DIM, activation="relu", name="encoder_dense1")(x)
    x = layers.Dense(AE_ENCODING_DIM, activation="relu", name="bottleneck")(x)

    # Décodeur
    x = layers.Dense(AE_HIDDEN_DIM, activation="relu", name="decoder_dense1")(x)
    outputs = layers.Dense(input_dim, activation="sigmoid", name="decoder_output")(x)

    autoencoder = Model(inputs, outputs, name="denoising_autoencoder")
    autoencoder.compile(
        optimizer="adam",
        loss="mse",
        metrics=["mae"]
    )

    print(f"  ✓ Architecture :")
    print(f"      Input({input_dim}) → Noise({AE_NOISE_FACTOR})")
    print(f"      → Dense({AE_HIDDEN_DIM}, relu)")
    print(f"      → Bottleneck({AE_ENCODING_DIM}, relu)")
    print(f"      → Dense({AE_HIDDEN_DIM}, relu)")
    print(f"      → Output({input_dim}, sigmoid)")
    print(f"  ✓ Optimiseur : Adam | Loss : MSE")

    autoencoder.summary()

    return autoencoder


def train_autoencoder(X_train, y_train, X_test, y_test):
    """
    Entraîne l'auto-encodeur exclusivement sur le trafic normal
    et calcule le seuil d'anomalie au 95ème centile.

    Args:
        X_train: Features d'entraînement (AVANT SMOTE, après RFE + scaling).
        y_train: Labels d'entraînement.
        X_test: Features de test.
        y_test: Labels de test.

    Returns:
        tuple: (autoencoder, threshold, ae_metrics)
    """
    # Filtrer uniquement le trafic normal pour l'entraînement
    normal_mask_train = y_train == 0
    X_normal_train = X_train[normal_mask_train]

    print(f"\n  ✓ Trafic normal (train) : {X_normal_train.shape[0]:,} échantillons")

    # Normaliser entre 0 et 1 pour l'auto-encodeur (sigmoid en sortie)
    from sklearn.preprocessing import MinMaxScaler
    ae_scaler = MinMaxScaler()
    X_normal_scaled = ae_scaler.fit_transform(X_normal_train)
    X_test_scaled = ae_scaler.transform(X_test)

    # Sauvegarder le scaler de l'AE
    ae_scaler_path = AUTOENCODER_MODEL_PATH.replace(".keras", "_scaler.joblib")
    joblib.dump(ae_scaler, ae_scaler_path)

    input_dim = X_normal_scaled.shape[1]
    autoencoder = build_autoencoder(input_dim)

    print("\n" + "=" * 70)
    print("  ENTRAÎNEMENT DE L'AUTO-ENCODEUR")
    print("=" * 70)
    print(f"  → Données normales : {X_normal_scaled.shape[0]:,} échantillons")
    print(f"  → Époques : {AE_EPOCHS} | Batch : {AE_BATCH_SIZE}")
    print("  → Entraînement en cours...\n")

    start_time = time.time()

    history = autoencoder.fit(
        X_normal_scaled, X_normal_scaled,
        epochs=AE_EPOCHS,
        batch_size=AE_BATCH_SIZE,
        validation_split=AE_VALIDATION_SPLIT,
        shuffle=True,
        verbose=1,
        callbacks=[
            keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=5,
                restore_best_weights=True,
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=3,
                min_lr=1e-6,
            ),
        ],
    )

    train_time = time.time() - start_time
    print(f"\n  ✓ Entraînement terminé en {train_time:.1f}s")

    # ── Calcul du seuil d'anomalie ──
    print("\n" + "=" * 70)
    print("  CALCUL DU SEUIL D'ANOMALIE")
    print("=" * 70)

    # Erreur de reconstruction sur les données normales d'entraînement
    reconstructed = autoencoder.predict(X_normal_scaled, verbose=0)
    mse_normal = np.mean(np.power(X_normal_scaled - reconstructed, 2), axis=1)

    threshold = np.percentile(mse_normal, AE_ANOMALY_PERCENTILE)
    print(f"  ✓ Seuil ({AE_ANOMALY_PERCENTILE}ème centile) : {threshold:.6f}")

    # ── Évaluation sur le test set ──
    print("\n  Évaluation sur le test set :")

    reconstructed_test = autoencoder.predict(X_test_scaled, verbose=0)
    mse_test = np.mean(np.power(X_test_scaled - reconstructed_test, 2), axis=1)

    # Prédictions : anomalie si erreur > seuil
    ae_predictions = (mse_test > threshold).astype(int)

    # Comparer avec les vrais labels
    ae_acc = accuracy_score(y_test, ae_predictions)
    ae_prec = precision_score(y_test, ae_predictions, average="weighted", zero_division=0)
    ae_rec = recall_score(y_test, ae_predictions, average="weighted", zero_division=0)
    ae_f1 = f1_score(y_test, ae_predictions, average="weighted", zero_division=0)

    print(f"\n  ┌─────────────────────────────────────────┐")
    print(f"  │   AUTO-ENCODEUR — MÉTRIQUES             │")
    print(f"  ├─────────────────────────────────────────┤")
    print(f"  │  Accuracy  : {ae_acc:.4f}                    │")
    print(f"  │  Precision : {ae_prec:.4f}                    │")
    print(f"  │  Recall    : {ae_rec:.4f}                    │")
    print(f"  │  F1-Score  : {ae_f1:.4f}                    │")
    print(f"  │  Seuil     : {threshold:.6f}              │")
    print(f"  └─────────────────────────────────────────┘")

    # Statistiques de détection
    normal_test = y_test == 0
    attack_test = y_test == 1
    normal_detected = (ae_predictions[normal_test] == 0).sum()
    attack_detected = (ae_predictions[attack_test] == 1).sum()
    print(f"\n  ✓ Trafic normal correctement identifié : {normal_detected}/{normal_test.sum()}")
    print(f"  ✓ Attaques détectées comme anomalies   : {attack_detected}/{attack_test.sum()}")

    # Sauvegarder
    autoencoder.save(AUTOENCODER_MODEL_PATH)
    joblib.dump(threshold, AE_THRESHOLD_PATH)
    print(f"\n  ✓ Auto-encodeur sauvegardé → {AUTOENCODER_MODEL_PATH}")
    print(f"  ✓ Seuil sauvegardé → {AE_THRESHOLD_PATH}")

    ae_metrics = {
        "accuracy": ae_acc,
        "precision": ae_prec,
        "recall": ae_rec,
        "f1_score": ae_f1,
        "threshold": threshold,
        "training_time_seconds": train_time,
    }

    return autoencoder, threshold, ae_metrics


# ══════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

def main():
    """
    Pipeline complet d'entraînement :
      1. Prétraitement des données
      2. Entraînement du Stacking Classifier
      3. Entraînement de l'Auto-encodeur
      4. Sauvegarde des métriques globales
    """
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + "  ENTRAÎNEMENT DES MODÈLES — Module B Security Engine".center(68) + "║")
    print("╚" + "═" * 68 + "╝\n")

    total_start = time.time()

    # ── 1. Prétraitement ──
    print("━" * 70)
    print("  PHASE 1 : Prétraitement des données")
    print("━" * 70)
    data = run_preprocessing()

    X_train = data["X_train"]
    y_train = data["y_train"]
    X_test = data["X_test"]
    y_test = data["y_test"]

    # ── 2. Stacking Classifier ──
    print("\n" + "━" * 70)
    print("  PHASE 2 : Entraînement du Stacking Classifier")
    print("━" * 70)
    stacking_model, stacking_metrics = train_stacking(
        X_train, y_train, X_test, y_test
    )

    # ── 3. Auto-encodeur ──
    # Note: On utilise les données AVANT SMOTE pour l'auto-encodeur
    # car il doit apprendre le profil du trafic normal réel
    print("\n" + "━" * 70)
    print("  PHASE 3 : Entraînement de l'Auto-encodeur")
    print("━" * 70)

    # Recharger les données pré-SMOTE pour l'AE
    from preprocess import load_data, clean_data, encode_categorical, scale_features
    df_train, df_test = load_data()
    df_train, df_test = clean_data(df_train, df_test)
    df_train, df_test, _ = encode_categorical(df_train, df_test)

    X_train_raw = df_train.drop(columns=["label"])
    y_train_raw = df_train["label"]
    X_test_raw = df_test.drop(columns=["label"])
    y_test_raw = df_test["label"]

    # Utiliser le scaler et les features du preprocessing
    scaler = data["scaler"]
    selected_features = data["selected_features"]

    X_train_scaled = pd.DataFrame(
        scaler.transform(X_train_raw),
        columns=X_train_raw.columns
    )[selected_features]

    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test_raw),
        columns=X_test_raw.columns
    )[selected_features]

    autoencoder, threshold, ae_metrics = train_autoencoder(
        X_train_scaled, y_train_raw, X_test_scaled, y_test_raw
    )

    # ── 4. Sauvegarde des métriques globales ──
    all_metrics = {
        "stacking_classifier": stacking_metrics,
        "autoencoder": ae_metrics,
        "selected_features": data["selected_features"],
    }
    joblib.dump(all_metrics, TRAINING_METRICS_PATH)

    total_time = time.time() - total_start

    # ── Résumé final ──
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + "  RÉSUMÉ FINAL DE L'ENTRAÎNEMENT".center(68) + "║")
    print("╠" + "═" * 68 + "╣")
    print(f"║  Stacking Classifier :".ljust(69) + "║")
    print(f"║    Accuracy  = {stacking_metrics['accuracy']:.4f}".ljust(69) + "║")
    print(f"║    Precision = {stacking_metrics['precision']:.4f}".ljust(69) + "║")
    print(f"║    Recall    = {stacking_metrics['recall']:.4f}".ljust(69) + "║")
    print(f"║    F1-Score  = {stacking_metrics['f1_score']:.4f}".ljust(69) + "║")
    print(f"║".ljust(69) + "║")
    print(f"║  Auto-encodeur (zero-day) :".ljust(69) + "║")
    print(f"║    Accuracy  = {ae_metrics['accuracy']:.4f}".ljust(69) + "║")
    print(f"║    Seuil     = {ae_metrics['threshold']:.6f}".ljust(69) + "║")
    print(f"║".ljust(69) + "║")
    print(f"║  Temps total : {total_time:.1f}s".ljust(69) + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n✅ Tous les modèles sont entraînés et sauvegardés.")
    print("   Lancez l'API : python -m uvicorn main:app --reload")


if __name__ == "__main__":
    main()
