"""
============================================================================
Module B — Security Engine | Pipeline de Prétraitement (preprocess.py)
============================================================================
Ce script implémente le pipeline complet de prétraitement des données
UNSW-NB15 pour le moteur de détection d'intrusions :

  1. Chargement et nettoyage des données
  2. Encodage des variables catégorielles (LabelEncoder)
  3. Normalisation (StandardScaler)
  4. Sélection de features par RFE (Recursive Feature Elimination)
  5. Équilibrage des classes par SMOTE (sur train uniquement)
  6. Sauvegarde des artefacts pour réutilisation à l'inférence

Auteur  : Module B — Security Engine
Projet  : NIDS Cyber-IA (Cahier des Charges)
============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
import joblib
import time

from config import (
    TRAIN_CSV, TEST_CSV, COLUMNS_TO_DROP, CATEGORICAL_COLUMNS,
    TARGET_COLUMN, RFE_N_FEATURES, SMOTE_RANDOM_STATE, SMOTE_K_NEIGHBORS,
    RANDOM_STATE, LABEL_ENCODERS_PATH, SCALER_PATH, RFE_SELECTOR_PATH,
    SELECTED_FEATURES_PATH, MODELS_DIR
)


def load_data():
    """
    Charge les jeux de données d'entraînement et de test.

    Returns:
        tuple: (df_train, df_test) DataFrames bruts.
    """
    print("=" * 70)
    print("  ÉTAPE 1 : Chargement des données")
    print("=" * 70)

    df_train = pd.read_csv(TRAIN_CSV)
    df_test = pd.read_csv(TEST_CSV)

    print(f"  ✓ Train set : {df_train.shape[0]:,} lignes × {df_train.shape[1]} colonnes")
    print(f"  ✓ Test set  : {df_test.shape[0]:,} lignes × {df_test.shape[1]} colonnes")
    print(f"  ✓ Distribution train (label) :")
    print(f"      Normal (0) : {(df_train[TARGET_COLUMN] == 0).sum():,}")
    print(f"      Attaque (1): {(df_train[TARGET_COLUMN] == 1).sum():,}")

    return df_train, df_test


def clean_data(df_train, df_test):
    """
    Nettoie les données : suppression des colonnes inutiles,
    remplacement des infinis et des NaN.

    Args:
        df_train: DataFrame d'entraînement.
        df_test: DataFrame de test.

    Returns:
        tuple: (df_train, df_test) nettoyés.
    """
    print("\n" + "=" * 70)
    print("  ÉTAPE 2 : Nettoyage des données")
    print("=" * 70)

    # Supprimer les colonnes non pertinentes (id, attack_cat)
    cols_to_drop_present = [c for c in COLUMNS_TO_DROP if c in df_train.columns]
    df_train = df_train.drop(columns=cols_to_drop_present)
    df_test = df_test.drop(columns=cols_to_drop_present)
    print(f"  ✓ Colonnes supprimées : {cols_to_drop_present}")

    # Remplacement des valeurs infinies par NaN, puis par la médiane
    for df_name, df in [("Train", df_train), ("Test", df_test)]:
        num_cols = df.select_dtypes(include=[np.number]).columns
        inf_count = np.isinf(df[num_cols]).sum().sum()
        if inf_count > 0:
            df[num_cols] = df[num_cols].replace([np.inf, -np.inf], np.nan)
            print(f"  ✓ {df_name} : {inf_count} valeurs infinies remplacées")

        nan_count = df.isnull().sum().sum()
        if nan_count > 0:
            df[num_cols] = df[num_cols].fillna(df[num_cols].median())
            print(f"  ✓ {df_name} : {nan_count} valeurs NaN remplacées par la médiane")
        else:
            print(f"  ✓ {df_name} : Aucune valeur manquante détectée")

    print(f"  ✓ Dimensions après nettoyage : {df_train.shape[1]} colonnes")

    return df_train, df_test


def encode_categorical(df_train, df_test):
    """
    Encode les variables catégorielles avec LabelEncoder.
    Sauvegarde les encodeurs pour réutilisation à l'inférence.

    Args:
        df_train: DataFrame d'entraînement.
        df_test: DataFrame de test.

    Returns:
        tuple: (df_train, df_test, label_encoders)
    """
    print("\n" + "=" * 70)
    print("  ÉTAPE 3 : Encodage des variables catégorielles")
    print("=" * 70)

    label_encoders = {}

    for col in CATEGORICAL_COLUMNS:
        if col not in df_train.columns:
            print(f"  ⚠ Colonne '{col}' absente — ignorée")
            continue

        le = LabelEncoder()

        # Combiner les valeurs uniques des deux sets pour éviter les erreurs
        # sur des catégories présentes uniquement dans le test set
        all_values = pd.concat([df_train[col], df_test[col]]).unique()
        le.fit(all_values)

        df_train[col] = le.transform(df_train[col])
        df_test[col] = le.transform(df_test[col])

        label_encoders[col] = le
        print(f"  ✓ '{col}' encodé — {len(le.classes_)} catégories")

    # Sauvegarder les encodeurs
    joblib.dump(label_encoders, LABEL_ENCODERS_PATH)
    print(f"\n  ✓ Encodeurs sauvegardés → {LABEL_ENCODERS_PATH}")

    return df_train, df_test, label_encoders


def scale_features(X_train, X_test):
    """
    Normalise les features numériques avec StandardScaler.

    Args:
        X_train: Features d'entraînement.
        X_test: Features de test.

    Returns:
        tuple: (X_train_scaled, X_test_scaled, scaler)
    """
    print("\n" + "=" * 70)
    print("  ÉTAPE 4 : Normalisation (StandardScaler)")
    print("=" * 70)

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index
    )

    # Sauvegarder le scaler
    joblib.dump(scaler, SCALER_PATH)
    print(f"  ✓ StandardScaler ajusté sur {X_train.shape[1]} features")
    print(f"  ✓ Scaler sauvegardé → {SCALER_PATH}")

    return X_train_scaled, X_test_scaled, scaler


def select_features_rfe(X_train, y_train, X_test):
    """
    Sélection de features par RFE (Recursive Feature Elimination)
    avec un RandomForestClassifier comme estimateur.
    Objectif : conserver 15-20 features couvrant ≥ 95% de la variance.

    Args:
        X_train: Features d'entraînement (scalées).
        y_train: Labels d'entraînement.
        X_test: Features de test (scalées).

    Returns:
        tuple: (X_train_selected, X_test_selected, selected_features)
    """
    print("\n" + "=" * 70)
    print("  ÉTAPE 5 : Sélection de features (RFE)")
    print("=" * 70)
    print(f"  → Objectif : sélectionner {RFE_N_FEATURES} features les plus importantes")

    start_time = time.time()

    # Estimateur pour RFE
    rf_estimator = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    # RFE
    rfe = RFE(
        estimator=rf_estimator,
        n_features_to_select=RFE_N_FEATURES,
        step=1,
        verbose=0
    )

    rfe.fit(X_train, y_train)

    # Features sélectionnées
    selected_mask = rfe.support_
    selected_features = X_train.columns[selected_mask].tolist()

    X_train_selected = X_train[selected_features]
    X_test_selected = X_test[selected_features]

    elapsed = time.time() - start_time

    print(f"  ✓ RFE terminé en {elapsed:.1f}s")
    print(f"  ✓ Features sélectionnées ({len(selected_features)}) :")
    for i, feat in enumerate(selected_features, 1):
        ranking = rfe.ranking_[X_train.columns.tolist().index(feat)]
        print(f"      {i:2d}. {feat:<25s} (rang: {ranking})")

    # Calculer l'importance relative des features sélectionnées
    rf_estimator.fit(X_train_selected, y_train)
    importances = rf_estimator.feature_importances_
    total_importance = importances.sum()
    print(f"\n  ✓ Importance cumulée des features sélectionnées : {total_importance * 100:.1f}%")

    # Sauvegarder
    joblib.dump(rfe, RFE_SELECTOR_PATH)
    joblib.dump(selected_features, SELECTED_FEATURES_PATH)
    print(f"  ✓ Sélecteur RFE sauvegardé → {RFE_SELECTOR_PATH}")
    print(f"  ✓ Liste des features sauvegardée → {SELECTED_FEATURES_PATH}")

    return X_train_selected, X_test_selected, selected_features


def apply_smote(X_train, y_train):
    """
    Applique SMOTE pour équilibrer les classes sur le train set.
    ⚠ SMOTE n'est JAMAIS appliqué sur le test set (pas de data leakage).

    Args:
        X_train: Features d'entraînement (après RFE).
        y_train: Labels d'entraînement.

    Returns:
        tuple: (X_train_resampled, y_train_resampled)
    """
    print("\n" + "=" * 70)
    print("  ÉTAPE 6 : Équilibrage des classes (SMOTE)")
    print("=" * 70)

    print(f"  → Distribution AVANT SMOTE :")
    for label in sorted(y_train.unique()):
        count = (y_train == label).sum()
        pct = count / len(y_train) * 100
        name = "Normal" if label == 0 else "Attaque"
        print(f"      {name} ({label}) : {count:,} ({pct:.1f}%)")

    smote = SMOTE(
        random_state=SMOTE_RANDOM_STATE,
        k_neighbors=SMOTE_K_NEIGHBORS
    )

    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    print(f"\n  → Distribution APRÈS SMOTE :")
    for label in sorted(y_resampled.unique()):
        count = (y_resampled == label).sum()
        pct = count / len(y_resampled) * 100
        name = "Normal" if label == 0 else "Attaque"
        print(f"      {name} ({label}) : {count:,} ({pct:.1f}%)")

    print(f"\n  ✓ Taille du train set : {len(X_train):,} → {len(X_resampled):,}")

    return X_resampled, y_resampled


def run_preprocessing():
    """
    Exécute le pipeline complet de prétraitement.

    Returns:
        dict: Dictionnaire contenant toutes les données prétraitées et artefacts.
    """
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + "  PIPELINE DE PRÉTRAITEMENT — Module B Security Engine".center(68) + "║")
    print("╚" + "═" * 68 + "╝\n")

    start_total = time.time()

    # 1. Chargement
    df_train, df_test = load_data()

    # 2. Nettoyage
    df_train, df_test = clean_data(df_train, df_test)

    # 3. Encodage catégoriel
    df_train, df_test, label_encoders = encode_categorical(df_train, df_test)

    # 4. Séparation features / target
    X_train = df_train.drop(columns=[TARGET_COLUMN])
    y_train = df_train[TARGET_COLUMN]
    X_test = df_test.drop(columns=[TARGET_COLUMN])
    y_test = df_test[TARGET_COLUMN]

    print(f"\n  → Features d'entraînement : {X_train.shape}")
    print(f"  → Features de test        : {X_test.shape}")

    # 5. Normalisation
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)

    # 6. Sélection de features (RFE)
    X_train_rfe, X_test_rfe, selected_features = select_features_rfe(
        X_train_scaled, y_train, X_test_scaled
    )

    # 7. SMOTE (uniquement sur train)
    X_train_final, y_train_final = apply_smote(X_train_rfe, y_train)

    total_time = time.time() - start_total

    print("\n" + "=" * 70)
    print("  RÉSUMÉ DU PRÉTRAITEMENT")
    print("=" * 70)
    print(f"  ✓ Features originales     : {X_train.shape[1]}")
    print(f"  ✓ Features sélectionnées  : {len(selected_features)}")
    print(f"  ✓ Train set final         : {X_train_final.shape}")
    print(f"  ✓ Test set final          : {X_test_rfe.shape}")
    print(f"  ✓ Temps total             : {total_time:.1f}s")
    print(f"  ✓ Artefacts sauvegardés dans : {MODELS_DIR}")
    print("=" * 70)

    return {
        "X_train": X_train_final,
        "y_train": y_train_final,
        "X_test": X_test_rfe,
        "y_test": y_test,
        "selected_features": selected_features,
        "label_encoders": label_encoders,
        "scaler": scaler,
    }


# ──────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_preprocessing()
    print("\n✅ Prétraitement terminé avec succès.")
    print(f"   Prêt pour l'entraînement (train_model.py)")
