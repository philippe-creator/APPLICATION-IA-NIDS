// Moteur ML Simulé - Basé sur le cahier des charges UNSW-NB15
// Modèle Hybrid Ensemble (LightGBM + XGBoost + RandomForest) + Auto-encodeur

import type { NetworkFlow, AttackCategory, ShapExplanation, ThreatLevel } from './types'

// Features importantes identifiées par RFE (Recursive Feature Elimination)
const IMPORTANT_FEATURES = [
  'sttl',           // Time-To-Live source
  'sbytes',         // Bytes envoyés par source
  'sload',          // Charge source
  'dur',            // Durée de la transaction
  'ct_dst_src_ltm', // Connexions source-destination récentes
  'spkts',          // Paquets source
  'dbytes',         // Bytes destination
  'dload',          // Charge destination
  'dpkts',          // Paquets destination
  'dttl',           // TTL destination
] as const

// Poids simulés des modèles ensemble
const ENSEMBLE_WEIGHTS = {
  lightgbm: 0.40,
  xgboost: 0.35,
  randomforest: 0.25,
}

// Seuils de détection par catégorie
const DETECTION_THRESHOLDS: Record<AttackCategory, number> = {
  Normal: 0.3,
  DoS: 0.65,
  Exploit: 0.70,
  Fuzzers: 0.60,
  Reconnaissance: 0.55,
  Worms: 0.80,
  Backdoors: 0.85,
  Shellcode: 0.82,
  Generic: 0.50,
  Analysis: 0.45,
}

// Statistiques de référence pour normalisation (basées sur UNSW-NB15)
const FEATURE_STATS = {
  sttl: { mean: 64, std: 32 },
  sbytes: { mean: 1500, std: 5000 },
  sload: { mean: 500, std: 2000 },
  dur: { mean: 2.5, std: 5 },
  ct_dst_src_ltm: { mean: 3, std: 5 },
  spkts: { mean: 15, std: 50 },
  dbytes: { mean: 2000, std: 8000 },
  dload: { mean: 600, std: 2500 },
  dpkts: { mean: 20, std: 60 },
  dttl: { mean: 64, std: 32 },
}

// Normaliser une feature
function normalizeFeature(value: number, feature: keyof typeof FEATURE_STATS): number {
  const { mean, std } = FEATURE_STATS[feature]
  return (value - mean) / (std || 1)
}

// Simuler la prédiction LightGBM
function predictLightGBM(flow: NetworkFlow): { category: AttackCategory; confidence: number } {
  const scores: Partial<Record<AttackCategory, number>> = {}
  
  // Calcul des scores basé sur les patterns d'attaque
  const normalizedSload = normalizeFeature(flow.sload, 'sload')
  const normalizedSbytes = normalizeFeature(flow.sbytes, 'sbytes')
  const normalizedDur = normalizeFeature(flow.dur, 'dur')
  const normalizedSpkts = normalizeFeature(flow.spkts, 'spkts')
  
  // DoS: charge élevée, beaucoup de paquets, durée courte
  scores.DoS = Math.min(0.95, Math.max(0, 
    0.3 * sigmoid(normalizedSload) + 
    0.3 * sigmoid(normalizedSpkts) + 
    0.2 * sigmoid(-normalizedDur) +
    0.2 * sigmoid(normalizedSbytes)
  ))
  
  // Reconnaissance: durée très courte, patterns répétitifs
  scores.Reconnaissance = Math.min(0.9, Math.max(0,
    0.4 * sigmoid(-normalizedDur * 2) +
    0.3 * sigmoid(normalizeFeature(flow.ct_dst_src_ltm, 'ct_dst_src_ltm')) +
    0.3 * (flow.dur < 0.1 ? 0.8 : 0.2)
  ))
  
  // Exploit: payload suspect
  scores.Exploit = Math.min(0.9, Math.max(0,
    0.4 * sigmoid(normalizedSbytes) +
    0.3 * (flow.sttl < 40 || flow.sttl > 200 ? 0.7 : 0.2) +
    0.3 * sigmoid(normalizeFeature(flow.dload, 'dload'))
  ))
  
  // Normal: inverse des scores d'attaque
  scores.Normal = Math.max(0.1, 1 - Math.max(scores.DoS || 0, scores.Reconnaissance || 0, scores.Exploit || 0))
  
  // Autres catégories avec bruit
  scores.Fuzzers = Math.random() * 0.3
  scores.Worms = Math.random() * 0.1
  scores.Backdoors = Math.random() * 0.1
  scores.Shellcode = Math.random() * 0.1
  scores.Generic = Math.random() * 0.2
  scores.Analysis = Math.random() * 0.15
  
  // Trouver la catégorie avec le score le plus élevé
  let maxCategory: AttackCategory = 'Normal'
  let maxScore = 0
  
  for (const [cat, score] of Object.entries(scores)) {
    if (score && score > maxScore) {
      maxScore = score
      maxCategory = cat as AttackCategory
    }
  }
  
  return { category: maxCategory, confidence: maxScore }
}

// Simuler la prédiction XGBoost
function predictXGBoost(flow: NetworkFlow): { category: AttackCategory; confidence: number } {
  const lgbmResult = predictLightGBM(flow)
  // XGBoost a des patterns légèrement différents
  const noise = (Math.random() - 0.5) * 0.1
  return {
    category: lgbmResult.category,
    confidence: Math.min(0.98, Math.max(0.1, lgbmResult.confidence + noise))
  }
}

// Simuler la prédiction Random Forest
function predictRandomForest(flow: NetworkFlow): { category: AttackCategory; confidence: number } {
  const lgbmResult = predictLightGBM(flow)
  const noise = (Math.random() - 0.5) * 0.15
  return {
    category: lgbmResult.category,
    confidence: Math.min(0.95, Math.max(0.1, lgbmResult.confidence + noise))
  }
}

// Fonction sigmoid pour normalisation
function sigmoid(x: number): number {
  return 1 / (1 + Math.exp(-x))
}

// Auto-encodeur pour détection Zero-day
function computeReconstructionError(flow: NetworkFlow): number {
  // Simuler l'erreur de reconstruction basée sur les anomalies
  const features = [
    normalizeFeature(flow.sttl, 'sttl'),
    normalizeFeature(flow.sbytes, 'sbytes'),
    normalizeFeature(flow.sload, 'sload'),
    normalizeFeature(flow.dur, 'dur'),
    normalizeFeature(flow.spkts, 'spkts'),
  ]
  
  // Calculer la "distance" par rapport au profil normal
  const anomalyScore = features.reduce((sum, f) => sum + Math.abs(f), 0) / features.length
  
  // Ajouter du bruit réaliste
  return anomalyScore * (0.8 + Math.random() * 0.4)
}

// Générer les valeurs SHAP pour explicabilité
export function computeShapValues(flow: NetworkFlow, prediction: AttackCategory): ShapExplanation[] {
  const explanations: ShapExplanation[] = []
  
  const featureValues: Record<string, { value: number; description: string }> = {
    sttl: { value: flow.sttl, description: 'Time-To-Live source - topologie réseau' },
    sbytes: { value: flow.sbytes, description: 'Volume de données source' },
    sload: { value: flow.sload, description: 'Charge réseau source' },
    dur: { value: flow.dur, description: 'Durée de la transaction' },
    ct_dst_src_ltm: { value: flow.ct_dst_src_ltm, description: 'Connexions récentes similaires' },
    spkts: { value: flow.spkts, description: 'Nombre de paquets source' },
    dbytes: { value: flow.dbytes, description: 'Volume de données destination' },
    dload: { value: flow.dload, description: 'Charge réseau destination' },
    dpkts: { value: flow.dpkts, description: 'Nombre de paquets destination' },
  }
  
  // Calculer les contributions SHAP simulées
  for (const [feature, { value, description }] of Object.entries(featureValues)) {
    const normalized = normalizeFeature(value, feature as keyof typeof FEATURE_STATS)
    let shapValue = 0
    let contribution: 'positive' | 'negative' = 'positive'
    
    switch (prediction) {
      case 'DoS':
        if (feature === 'sload' || feature === 'spkts' || feature === 'sbytes') {
          shapValue = Math.abs(normalized) * 0.3 + Math.random() * 0.1
          contribution = normalized > 0 ? 'positive' : 'negative'
        } else if (feature === 'dur') {
          shapValue = Math.abs(normalized) * 0.2
          contribution = normalized < 0 ? 'positive' : 'negative'
        } else {
          shapValue = Math.random() * 0.1
          contribution = Math.random() > 0.5 ? 'positive' : 'negative'
        }
        break
        
      case 'Reconnaissance':
        if (feature === 'dur' || feature === 'ct_dst_src_ltm') {
          shapValue = Math.abs(normalized) * 0.35 + Math.random() * 0.1
          contribution = 'positive'
        } else {
          shapValue = Math.random() * 0.1
          contribution = Math.random() > 0.5 ? 'positive' : 'negative'
        }
        break
        
      case 'Exploit':
        if (feature === 'sbytes' || feature === 'sttl') {
          shapValue = Math.abs(normalized) * 0.3 + Math.random() * 0.1
          contribution = 'positive'
        } else {
          shapValue = Math.random() * 0.1
          contribution = Math.random() > 0.5 ? 'positive' : 'negative'
        }
        break
        
      default:
        shapValue = Math.random() * 0.15
        contribution = Math.random() > 0.5 ? 'positive' : 'negative'
    }
    
    explanations.push({
      feature,
      value,
      shapValue: Math.min(0.5, shapValue),
      contribution,
      description,
    })
  }
  
  // Trier par importance absolue
  return explanations.sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue))
}

// Prédiction ensemble complète
export interface MLPrediction {
  finalPrediction: AttackCategory
  confidence: number
  isAnomaly: boolean
  reconstructionError: number
  ensembleVotes: {
    lightgbm: { category: AttackCategory; confidence: number }
    xgboost: { category: AttackCategory; confidence: number }
    randomforest: { category: AttackCategory; confidence: number }
  }
  shapExplanations: ShapExplanation[]
  threatLevel: ThreatLevel
  riskScore: number
}

export function predictEnsemble(flow: NetworkFlow): MLPrediction {
  // Obtenir les prédictions de chaque modèle
  const lgbm = predictLightGBM(flow)
  const xgb = predictXGBoost(flow)
  const rf = predictRandomForest(flow)
  
  // Voting pondéré
  const votes: Record<AttackCategory, number> = {
    Normal: 0, DoS: 0, Exploit: 0, Fuzzers: 0, Reconnaissance: 0,
    Worms: 0, Backdoors: 0, Shellcode: 0, Generic: 0, Analysis: 0,
  }
  
  votes[lgbm.category] += lgbm.confidence * ENSEMBLE_WEIGHTS.lightgbm
  votes[xgb.category] += xgb.confidence * ENSEMBLE_WEIGHTS.xgboost
  votes[rf.category] += rf.confidence * ENSEMBLE_WEIGHTS.randomforest
  
  // Trouver la catégorie gagnante
  let finalCategory: AttackCategory = 'Normal'
  let maxVote = 0
  
  for (const [cat, vote] of Object.entries(votes)) {
    if (vote > maxVote) {
      maxVote = vote
      finalCategory = cat as AttackCategory
    }
  }
  
  // Calculer l'erreur de reconstruction (auto-encodeur)
  const reconstructionError = computeReconstructionError(flow)
  const anomalyThreshold = 1.5 // 95ème percentile simulé
  const isAnomaly = reconstructionError > anomalyThreshold
  
  // Si l'auto-encodeur détecte une anomalie mais le classifier dit Normal
  if (isAnomaly && finalCategory === 'Normal') {
    finalCategory = 'Analysis' // Potentielle attaque Zero-day
    maxVote = 0.6
  }
  
  // Calculer le niveau de menace
  const threatLevel = computeThreatLevel(finalCategory, maxVote)
  
  // Score de risque global
  const riskScore = computeRiskScore(finalCategory, maxVote, reconstructionError)
  
  // Générer les explications SHAP
  const shapExplanations = computeShapValues(flow, finalCategory)
  
  return {
    finalPrediction: finalCategory,
    confidence: maxVote,
    isAnomaly,
    reconstructionError,
    ensembleVotes: {
      lightgbm: lgbm,
      xgboost: xgb,
      randomforest: rf,
    },
    shapExplanations,
    threatLevel,
    riskScore,
  }
}

function computeThreatLevel(category: AttackCategory, confidence: number): ThreatLevel {
  if (category === 'Normal') return 'low'
  
  const severityMap: Record<AttackCategory, number> = {
    Normal: 0,
    Analysis: 1,
    Generic: 2,
    Fuzzers: 3,
    Reconnaissance: 4,
    DoS: 6,
    Exploit: 7,
    Backdoors: 8,
    Shellcode: 9,
    Worms: 10,
  }
  
  const severity = severityMap[category] || 0
  const adjustedSeverity = severity * confidence
  
  if (adjustedSeverity >= 7) return 'critical'
  if (adjustedSeverity >= 5) return 'high'
  if (adjustedSeverity >= 3) return 'medium'
  return 'low'
}

function computeRiskScore(category: AttackCategory, confidence: number, reconstructionError: number): number {
  const baseScore = category === 'Normal' ? 10 : 50
  const confidenceBonus = confidence * 30
  const anomalyBonus = Math.min(reconstructionError * 10, 20)
  
  return Math.min(100, baseScore + confidenceBonus + anomalyBonus)
}

// Métriques de performance du modèle
export interface ModelMetrics {
  accuracy: number
  precision: number
  recall: number
  f1Score: number
  falsePositiveRate: number
  truePositiveRate: number
  aucRoc: number
  inferenceLatency: number
  
  // Par catégorie
  perClassMetrics: Record<AttackCategory, {
    precision: number
    recall: number
    f1Score: number
    support: number
  }>
}

// Générer des métriques réalistes basées sur les benchmarks UNSW-NB15
export function generateModelMetrics(): ModelMetrics {
  return {
    accuracy: 98.2 + Math.random() * 1.5,
    precision: 97.5 + Math.random() * 2,
    recall: 98.0 + Math.random() * 1.5,
    f1Score: 97.8 + Math.random() * 1.8,
    falsePositiveRate: 0.5 + Math.random() * 1,
    truePositiveRate: 98.5 + Math.random() * 1,
    aucRoc: 0.985 + Math.random() * 0.01,
    inferenceLatency: 15 + Math.random() * 20,
    
    perClassMetrics: {
      Normal: { precision: 99.2, recall: 98.8, f1Score: 99.0, support: 37000 },
      DoS: { precision: 98.5, recall: 99.2, f1Score: 98.8, support: 12264 },
      Exploit: { precision: 96.8, recall: 95.5, f1Score: 96.1, support: 33393 },
      Fuzzers: { precision: 95.2, recall: 94.8, f1Score: 95.0, support: 18184 },
      Reconnaissance: { precision: 97.1, recall: 96.5, f1Score: 96.8, support: 10491 },
      Worms: { precision: 89.5, recall: 85.2, f1Score: 87.3, support: 130 },
      Backdoors: { precision: 92.3, recall: 88.7, f1Score: 90.5, support: 1746 },
      Shellcode: { precision: 93.1, recall: 91.2, f1Score: 92.1, support: 1133 },
      Generic: { precision: 97.8, recall: 97.2, f1Score: 97.5, support: 40000 },
      Analysis: { precision: 91.5, recall: 89.8, f1Score: 90.6, support: 2000 },
    },
  }
}
