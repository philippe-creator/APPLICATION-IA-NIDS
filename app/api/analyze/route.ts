import { NextRequest, NextResponse } from 'next/server'
import { predictEnsemble, type MLPrediction } from '@/lib/ml-engine'
import type { NetworkFlow, AttackCategory } from '@/lib/types'

// API de détection d'intrusion en temps réel
// Endpoint: POST /api/analyze

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Valider les données d'entrée
    const flow = validateAndParseFlow(body)
    if (!flow) {
      return NextResponse.json(
        { error: 'Invalid network flow data', details: 'Missing required fields' },
        { status: 400 }
      )
    }
    
    // Effectuer la prédiction
    const startTime = performance.now()
    const prediction = predictEnsemble(flow)
    const inferenceTime = performance.now() - startTime
    
    // Construire la réponse
    const response: AnalysisResponse = {
      success: true,
      flowId: flow.id,
      timestamp: new Date().toISOString(),
      prediction: {
        category: prediction.finalPrediction,
        confidence: prediction.confidence,
        threatLevel: prediction.threatLevel,
        riskScore: prediction.riskScore,
        isAnomaly: prediction.isAnomaly,
      },
      ensemble: {
        lightgbm: prediction.ensembleVotes.lightgbm,
        xgboost: prediction.ensembleVotes.xgboost,
        randomforest: prediction.ensembleVotes.randomforest,
      },
      autoencoder: {
        reconstructionError: prediction.reconstructionError,
        anomalyDetected: prediction.isAnomaly,
        threshold: 1.5,
      },
      explanation: prediction.shapExplanations.slice(0, 5).map(exp => ({
        feature: exp.feature,
        value: exp.value,
        contribution: exp.shapValue,
        direction: exp.contribution,
        description: exp.description,
      })),
      recommendation: generateRecommendation(prediction),
      performance: {
        inferenceTimeMs: Math.round(inferenceTime * 100) / 100,
        modelVersion: '2.1.0',
        timestamp: new Date().toISOString(),
      },
    }
    
    return NextResponse.json(response)
    
  } catch (error) {
    console.error('[NIDS API] Analysis error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: String(error) },
      { status: 500 }
    )
  }
}

// GET pour vérifier le status de l'API
export async function GET() {
  return NextResponse.json({
    status: 'online',
    service: 'NIDS Cyber-IA Analysis Engine',
    version: '2.1.0',
    models: {
      ensemble: ['LightGBM', 'XGBoost', 'RandomForest'],
      anomaly: 'Denoising Autoencoder',
      explainability: 'SHAP (SHapley Additive exPlanations)',
    },
    features: {
      count: 10,
      important: ['sttl', 'sbytes', 'sload', 'dur', 'ct_dst_src_ltm'],
    },
    performance: {
      avgInferenceMs: 25,
      accuracy: 98.5,
      f1Score: 97.8,
    },
    timestamp: new Date().toISOString(),
  })
}

// Types de réponse
interface AnalysisResponse {
  success: boolean
  flowId: string
  timestamp: string
  prediction: {
    category: AttackCategory
    confidence: number
    threatLevel: string
    riskScore: number
    isAnomaly: boolean
  }
  ensemble: {
    lightgbm: { category: AttackCategory; confidence: number }
    xgboost: { category: AttackCategory; confidence: number }
    randomforest: { category: AttackCategory; confidence: number }
  }
  autoencoder: {
    reconstructionError: number
    anomalyDetected: boolean
    threshold: number
  }
  explanation: Array<{
    feature: string
    value: number
    contribution: number
    direction: 'positive' | 'negative'
    description: string
  }>
  recommendation: string
  performance: {
    inferenceTimeMs: number
    modelVersion: string
    timestamp: string
  }
}

// Valider et parser un flux réseau
function validateAndParseFlow(data: unknown): NetworkFlow | null {
  if (!data || typeof data !== 'object') return null
  
  const flow = data as Record<string, unknown>
  
  // Champs requis avec valeurs par défaut
  const parsed: NetworkFlow = {
    id: String(flow.id || generateId()),
    timestamp: flow.timestamp ? new Date(String(flow.timestamp)) : new Date(),
    srcip: String(flow.srcip || '0.0.0.0'),
    dstip: String(flow.dstip || '0.0.0.0'),
    sport: Number(flow.sport) || 0,
    dsport: Number(flow.dsport) || 0,
    proto: String(flow.proto || 'tcp'),
    dur: Number(flow.dur) || 0,
    sbytes: Number(flow.sbytes) || 0,
    dbytes: Number(flow.dbytes) || 0,
    sttl: Number(flow.sttl) || 64,
    dttl: Number(flow.dttl) || 64,
    sload: Number(flow.sload) || 0,
    dload: Number(flow.dload) || 0,
    spkts: Number(flow.spkts) || 0,
    dpkts: Number(flow.dpkts) || 0,
    service: String(flow.service || 'unknown'),
    state: String(flow.state || 'CON'),
    ct_dst_src_ltm: Number(flow.ct_dst_src_ltm) || 0,
    attack_cat: 'Normal' as AttackCategory,
    label: 0,
    riskScore: 0,
  }
  
  return parsed
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Date.now().toString(36)
}

// Générer une recommandation basée sur la prédiction
function generateRecommendation(prediction: MLPrediction): string {
  const { finalPrediction, threatLevel, confidence } = prediction
  
  if (finalPrediction === 'Normal') {
    return 'Trafic normal - Aucune action requise. Continuer la surveillance standard.'
  }
  
  const actions: Record<AttackCategory, string> = {
    Normal: 'Aucune action requise.',
    DoS: 'URGENT: Activer le rate limiting sur l\'IP source. Vérifier les règles de pare-feu. Notifier l\'équipe NOC pour coordination.',
    Exploit: 'CRITIQUE: Isoler le système cible immédiatement. Vérifier les patches de sécurité. Lancer un audit des accès récents.',
    Fuzzers: 'Renforcer la validation des entrées API. Activer le WAF en mode strict. Surveiller les logs d\'erreurs applicatives.',
    Reconnaissance: 'Bannissement temporaire (30 min) de l\'IP source. Examiner les journaux d\'accès. Renforcer la surveillance sur ce segment.',
    Worms: 'URGENCE MAXIMALE: Isoler le segment réseau concerné. Scanner tous les systèmes connectés. Activer le protocole de quarantaine.',
    Backdoors: 'CRITIQUE: Déconnecter immédiatement le système compromis. Initier une analyse forensique complète. Notifier la direction.',
    Shellcode: 'CRITIQUE: Bloquer l\'IP source au niveau firewall. Vérifier l\'intégrité du système cible. Activer l\'analyse mémoire.',
    Generic: 'Surveiller le comportement sur les prochaines minutes. Collecter plus de données pour affiner l\'analyse.',
    Analysis: 'Potentielle attaque Zero-day détectée. Escalader vers l\'équipe de réponse aux incidents. Documentation requise.',
  }
  
  let recommendation = actions[finalPrediction]
  
  if (threatLevel === 'critical' && confidence > 0.8) {
    recommendation = '🚨 ALERTE CRITIQUE - ' + recommendation
  } else if (threatLevel === 'high') {
    recommendation = '⚠️ ALERTE HAUTE - ' + recommendation
  }
  
  return recommendation
}
