"""
============================================================================
ML Analytics & Algorithm Documentation - NIDS Cyber-IA
============================================================================
Analyse détaillée des algorithmes ML et métriques de qualité pour dashboard.
Documentation des performances, caractéristiques et explications.
============================================================================
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
import json
import time
from datetime import datetime

class MLAnalyticsEngine:
    """Moteur d'analyse des algorithmes ML pour le dashboard industriel."""
    
    def __init__(self):
        self.algorithms_info = self._initialize_algorithms_info()
        self.metrics_definitions = self._initialize_metrics_definitions()
        
    def _initialize_algorithms_info(self) -> Dict[str, Any]:
        """Initialise les informations détaillées sur les algorithmes."""
        return {
            "stacking_classifier": {
                "name": "Stacking Classifier Hybride",
                "type": "Ensemble Learning",
                "description": "Combinaison de 3 algorithmes de base avec un méta-classifieur",
                "base_learners": {
                    "lightgbm": {
                        "name": "LightGBM",
                        "type": "Gradient Boosting",
                        "parameters": {
                            "n_estimators": 200,
                            "learning_rate": 0.05,
                            "max_depth": 7,
                            "num_leaves": 63,
                            "subsample": 0.8,
                            "colsample_bytree": 0.8
                        },
                        "strengths": [
                            "Rapide et efficace sur grands datasets",
                            "Gère nativement les valeurs manquantes",
                            "Optimisé pour GPU/CPU",
                            "Bonne performance sur données tabulaires"
                        ],
                        "weaknesses": [
                            "Peut surapprendre sur petits datasets",
                            "Moins interprétable que les modèles linéaires",
                            "Sensible aux hyperparamètres"
                        ]
                    },
                    "xgboost": {
                        "name": "XGBoost",
                        "type": "Gradient Boosting",
                        "parameters": {
                            "n_estimators": 200,
                            "learning_rate": 0.05,
                            "max_depth": 7,
                            "subsample": 0.8,
                            "colsample_bytree": 0.8,
                            "reg_alpha": 0.1,
                            "reg_lambda": 1.0
                        },
                        "strengths": [
                            "Très haute performance prédictive",
                            "Régularisation L1/L2 intégrée",
                            "Robuste et largement utilisé",
                            "Gère bien les déséquilibres de classes"
                        ],
                        "weaknesses": [
                            "Plus lent que LightGBM",
                            "Plus de mémoire requise",
                            "Complexité de réglage des hyperparamètres"
                        ]
                    },
                    "random_forest": {
                        "name": "Random Forest",
                        "type": "Bagging Ensemble",
                        "parameters": {
                            "n_estimators": 300,
                            "max_depth": 15,
                            "min_samples_split": 5,
                            "min_samples_leaf": 2
                        },
                        "strengths": [
                            "Très robuste au surapprentissage",
                            "Bonne interprétabilité (feature importance)",
                            "Parallélisable efficacement",
                            "Gère bien les données bruitées"
                        ],
                        "weaknesses": [
                            "Moins précis que gradient boosting",
                            "Plus lent à l'inférence",
                            "Moins efficace sur très grands datasets"
                        ]
                    }
                },
                "meta_classifier": {
                    "name": "Logistic Regression",
                    "type": "Linear Classifier",
                    "parameters": {
                        "C": 1.0,
                        "max_iter": 1000
                    },
                    "role": "Combine les prédictions des base learners",
                    "strengths": [
                        "Simple et interprétable",
                        "Rapide à l'entraînement",
                        "Bonne baseline pour méta-apprentissage",
                        "Probabilités bien calibrées"
                    ]
                },
                "architecture": {
                    "cross_validation": "5-fold CV",
                    "stacking_method": "predict_proba",
                    "ensemble_strategy": "Weighted voting via meta-learner"
                }
            },
            "autoencoder": {
                "name": "Denoising Autoencoder",
                "type": "Deep Learning - Anomaly Detection",
                "description": "Réseau neuronal non supervisé pour détection d'anomalies zero-day",
                "architecture": {
                    "input_dim": "Variable (nombre de features sélectionnées)",
                    "noise_factor": 0.1,
                    "layers": [
                        {"type": "Input", "size": "input_dim"},
                        {"type": "GaussianNoise", "noise": 0.1},
                        {"type": "Dense", "size": 64, "activation": "relu"},
                        {"type": "Dense", "size": 16, "activation": "relu"},  # Bottleneck
                        {"type": "Dense", "size": 64, "activation": "relu"},
                        {"type": "Dense", "size": "input_dim", "activation": "sigmoid"}
                    ]
                },
                "training": {
                    "optimizer": "Adam",
                    "loss_function": "Mean Squared Error (MSE)",
                    "epochs": 50,
                    "batch_size": 256,
                    "validation_split": 0.1,
                    "early_stopping": {
                        "monitor": "val_loss",
                        "patience": 5,
                        "restore_best_weights": True
                    },
                    "lr_scheduler": {
                        "type": "ReduceLROnPlateau",
                        "factor": 0.5,
                        "patience": 3
                    }
                },
                "anomaly_detection": {
                    "method": "Reconstruction Error",
                    "threshold_percentile": 95,
                    "training_data": "Uniquement trafic normal",
                    "scaling": "MinMaxScaler [0,1]",
                    "decision_rule": "error > threshold => anomaly"
                },
                "strengths": [
                    "Détection d'anomalies zero-day",
                    "Apprentissage non supervisé",
                    "Robuste aux nouveaux types d'attaques",
                    "Architecture simple et efficace"
                ],
                "weaknesses": [
                    "Nécessite beaucoup de données normales",
                    "Sensible au choix du seuil",
                    "Moins interprétable que les modèles linéaires",
                    "Requiert un prétraitement careful"
                ]
            }
        }
    
    def _initialize_metrics_definitions(self) -> Dict[str, Any]:
        """Initialise les définitions des métriques de qualité."""
        return {
            "accuracy": {
                "name": "Accuracy",
                "formula": "(TP + TN) / (TP + TN + FP + FN)",
                "description": "Proportion de prédictions correctes",
                "interpretation": {
                    "excellent": "> 0.95",
                    "good": "0.85-0.95",
                    "moderate": "0.70-0.85",
                    "poor": "< 0.70"
                },
                "limitations": [
                    "Peut être trompeuse sur datasets déséquilibrés",
                    "Ne différencie pas les types d'erreurs"
                ],
                "industrial_relevance": "Indicateur de performance globale pour SLA"
            },
            "precision": {
                "name": "Precision",
                "formula": "TP / (TP + FP)",
                "description": "Proportion de vraies attaques parmi les prédictions positives",
                "interpretation": {
                    "excellent": "> 0.90",
                    "good": "0.80-0.90",
                    "moderate": "0.65-0.80",
                    "poor": "< 0.65"
                },
                "importance": [
                    "Minimise les faux positifs",
                    "Crucial pour éviter les alertes excessives",
                    "Impact sur la confiance des opérateurs"
                ],
                "industrial_relevance": "Essentiel pour maintenir la confiance du système"
            },
            "recall": {
                "name": "Recall (Sensitivity)",
                "formula": "TP / (TP + FN)",
                "description": "Proportion d'attaques réelles détectées",
                "interpretation": {
                    "excellent": "> 0.90",
                    "good": "0.80-0.90",
                    "moderate": "0.65-0.80",
                    "poor": "< 0.65"
                },
                "importance": [
                    "Minimise les faux négatifs",
                    "Crucial pour ne pas manquer d'attaques",
                    "Impact sur la sécurité globale"
                ],
                "industrial_relevance": "Critique pour la sécurité industrielle"
            },
            "f1_score": {
                "name": "F1-Score",
                "formula": "2 × (Precision × Recall) / (Precision + Recall)",
                "description": "Moyenne harmonique de precision et recall",
                "interpretation": {
                    "excellent": "> 0.90",
                    "good": "0.80-0.90",
                    "moderate": "0.70-0.80",
                    "poor": "< 0.70"
                },
                "advantages": [
                    "Équilibre precision et recall",
                    "Robuste au déséquilibre des classes",
                    "Métrique unique pour comparaison"
                ],
                "industrial_relevance": "Indicateur de performance équilibré"
            },
            "auc_roc": {
                "name": "AUC-ROC",
                "description": "Area Under the Receiver Operating Characteristic Curve",
                "interpretation": {
                    "excellent": "> 0.95",
                    "good": "0.85-0.95",
                    "moderate": "0.70-0.85",
                    "poor": "< 0.70"
                },
                "advantages": [
                    "Indépendant du seuil de classification",
                    "Évalue la capacité de discrimination",
                    "Utile pour comparer les modèles"
                ]
            },
            "confusion_matrix": {
                "name": "Matrice de Confusion",
                "description": "Tableau des prédictions vs réalité",
                "components": {
                    "TP": "True Positive - Attaque correctement détectée",
                    "TN": "True Negative - Normal correctement identifié",
                    "FP": "False Positive - Normal identifié comme attaque",
                    "FN": "False Negative - Attaque non détectée"
                },
                "industrial_implications": {
                    "FP": "Alertes fausses → perte de confiance",
                    "FN": "Attaques manquées → risque de sécurité"
                }
            },
            "reconstruction_error": {
                "name": "Erreur de Reconstruction (Autoencoder)",
                "description": "MSE entre input et output de l'autoencodeur",
                "calculation": "mean((input - output)²)",
                "threshold": "95ème percentile des erreurs sur données normales",
                "interpretation": {
                    "low_error": "Pattern normal (bien appris)",
                    "high_error": "Anomalie (pattern inconnu)"
                }
            }
        }
    
    def get_algorithm_details(self, algorithm_name: str) -> Dict[str, Any]:
        """Retourne les détails d'un algorithme spécifique."""
        return self.algorithms_info.get(algorithm_name, {})
    
    def get_metric_explanation(self, metric_name: str) -> Dict[str, Any]:
        """Retourne l'explication d'une métrique."""
        return self.metrics_definitions.get(metric_name, {})
    
    def calculate_advanced_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, 
                                 y_proba: np.ndarray) -> Dict[str, float]:
        """Calcule des métriques avancées pour évaluation."""
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
            roc_auc_score, matthews_corrcoef, average_precision_score
        )
        
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, average='weighted', zero_division=0),
            "recall": recall_score(y_true, y_pred, average='weighted', zero_division=0),
            "f1_score": f1_score(y_true, y_pred, average='weighted', zero_division=0),
            "roc_auc": roc_auc_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else 0.5,
            "matthews_corrcoef": matthews_corrcoef(y_true, y_pred),
            "average_precision": average_precision_score(y_true, y_proba)
        }
        
        # Métriques spécifiques au contexte industriel
        tn, fp, fn, tp = self._calculate_confusion_matrix(y_true, y_pred)
        
        metrics.update({
            "false_positive_rate": fp / (fp + tn) if (fp + tn) > 0 else 0,
            "false_negative_rate": fn / (fn + tp) if (fn + tp) > 0 else 0,
            "true_positive_rate": tp / (tp + fn) if (tp + fn) > 0 else 0,
            "true_negative_rate": tn / (tn + fp) if (tn + fp) > 0 else 0,
            "detection_rate": tp / (tp + fn) if (tp + fn) > 0 else 0,
            "alert_accuracy": tp / (tp + fp) if (tp + fp) > 0 else 0
        })
        
        return metrics
    
    def _calculate_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[int, int, int, int]:
        """Calcule la matrice de confusion."""
        tp = np.sum((y_true == 1) & (y_pred == 1))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        return tn, fp, fn, tp
    
    def generate_model_report(self, model_metrics: Dict[str, Any], 
                            algorithm_name: str) -> Dict[str, Any]:
        """Génère un rapport détaillé sur le modèle."""
        algorithm_info = self.get_algorithm_details(algorithm_name)
        
        report = {
            "model_name": algorithm_info.get("name", "Unknown"),
            "algorithm_type": algorithm_info.get("type", "Unknown"),
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": model_metrics,
            "quality_assessment": self._assess_model_quality(model_metrics),
            "industrial_recommendations": self._generate_industrial_recommendations(model_metrics),
            "technical_specifications": algorithm_info
        }
        
        return report
    
    def _assess_model_quality(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Évalue la qualité du modèle selon les métriques."""
        assessment = {}
        
        # Accuracy
        acc = metrics.get("accuracy", 0)
        if acc > 0.95:
            assessment["accuracy"] = "Excellent"
        elif acc > 0.85:
            assessment["accuracy"] = "Good"
        elif acc > 0.70:
            assessment["accuracy"] = "Moderate"
        else:
            assessment["accuracy"] = "Poor"
        
        # F1-Score
        f1 = metrics.get("f1_score", 0)
        if f1 > 0.90:
            assessment["f1_score"] = "Excellent"
        elif f1 > 0.80:
            assessment["f1_score"] = "Good"
        elif f1 > 0.70:
            assessment["f1_score"] = "Moderate"
        else:
            assessment["f1_score"] = "Poor"
        
        # Taux d'erreurs (industriel)
        fpr = metrics.get("false_positive_rate", 0)
        fnr = metrics.get("false_negative_rate", 0)
        
        if fpr < 0.05 and fnr < 0.05:
            assessment["error_rates"] = "Excellent"
        elif fpr < 0.10 and fnr < 0.10:
            assessment["error_rates"] = "Good"
        elif fpr < 0.20 and fnr < 0.20:
            assessment["error_rates"] = "Moderate"
        else:
            assessment["error_rates"] = "Poor"
        
        return assessment
    
    def _generate_industrial_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Génère des recommandations pour contexte industriel."""
        recommendations = []
        
        fpr = metrics.get("false_positive_rate", 0)
        fnr = metrics.get("false_negative_rate", 0)
        accuracy = metrics.get("accuracy", 0)
        
        if fpr > 0.15:
            recommendations.append(
                "🔴 **Taux de faux positifs élevé** - Ajuster le seuil de décision "
                "ou améliorer la qualité des données pour réduire les fausses alertes"
            )
        
        if fnr > 0.15:
            recommendations.append(
                "🔴 **Taux de faux négatifs élevé** - Risque de sécurité critique. "
                "Considérer l'ajout de features ou l'optimisation des hyperparamètres"
            )
        
        if accuracy < 0.80:
            recommendations.append(
                "🟡 **Accuracy modérée** - Entraîner avec plus de données "
                "ou essayer d'autres algorithmes d'ensemble"
            )
        
        if fpr < 0.05 and fnr < 0.05:
            recommendations.append(
                "✅ **Performance excellente** - Modèle prêt pour déploiement industriel"
            )
        
        # Recommandations spécifiques
        recommendations.extend([
            "📊 **Monitoring continu** - Surveiller les métriques en production",
            "🔄 **Réentraînement régulier** - Mettre à jour avec de nouvelles données",
            "🧪 **Tests A/B** - Comparer avec d'autres modèles avant déploiement"
        ])
        
        return recommendations
    
    def create_feature_importance_analysis(self, feature_names: List[str], 
                                        importances: np.ndarray) -> Dict[str, Any]:
        """Crée une analyse de l'importance des features."""
        # Trier par importance
        sorted_idx = np.argsort(importances)[::-1]
        sorted_features = [feature_names[i] for i in sorted_idx]
        sorted_importances = importances[sorted_idx]
        
        # Analyse statistique
        total_importance = np.sum(importances)
        cumulative_importance = np.cumsum(sorted_importances)
        
        # Top features
        top_5_features = list(zip(sorted_features[:5], sorted_importances[:5]))
        
        return {
            "total_features": len(feature_names),
            "top_features": top_5_features,
            "cumulative_importance": {
                "top_5": cumulative_importance[4] / total_importance if len(cumulative_importance) > 4 else 1.0,
                "top_10": cumulative_importance[9] / total_importance if len(cumulative_importance) > 9 else 1.0,
                "top_20": cumulative_importance[19] / total_importance if len(cumulative_importance) > 19 else 1.0
            },
            "feature_analysis": {
                "most_important": sorted_features[0] if len(sorted_features) > 0 else None,
                "least_important": sorted_features[-1] if len(sorted_features) > 0 else None,
                "importance_distribution": {
                    "mean": np.mean(importances),
                    "std": np.std(importances),
                    "min": np.min(importances),
                    "max": np.max(importances)
                }
            }
        }

# Instance globale pour le dashboard
ml_analytics = MLAnalyticsEngine()
