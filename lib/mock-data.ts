import type { 
  NetworkFlow, 
  Alert, 
  AttackCategory, 
  ThreatLevel, 
  SystemMetrics, 
  TrafficStats,
  ShapExplanation,
  AIAgentMessage
} from './types'

// Générateur d'ID unique
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

// Catégories d'attaques avec poids pour simulation réaliste
const attackCategories: { category: AttackCategory; weight: number }[] = [
  { category: 'Normal', weight: 0.70 },
  { category: 'DoS', weight: 0.08 },
  { category: 'Reconnaissance', weight: 0.07 },
  { category: 'Exploit', weight: 0.05 },
  { category: 'Fuzzers', weight: 0.04 },
  { category: 'Generic', weight: 0.03 },
  { category: 'Backdoors', weight: 0.015 },
  { category: 'Shellcode', weight: 0.01 },
  { category: 'Worms', weight: 0.005 },
]

// Sélection pondérée d'une catégorie d'attaque
function selectAttackCategory(): AttackCategory {
  const random = Math.random()
  let cumulative = 0
  for (const { category, weight } of attackCategories) {
    cumulative += weight
    if (random <= cumulative) {
      return category
    }
  }
  return 'Normal'
}

// Génération d'une adresse IP aléatoire
function generateIP(internal = true): string {
  if (internal) {
    const prefixes = ['192.168.', '10.0.', '172.16.']
    const prefix = prefixes[Math.floor(Math.random() * prefixes.length)]
    return `${prefix}${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`
  }
  return `${Math.floor(Math.random() * 223) + 1}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`
}

// Services logistiques simulés
const services = ['ERP-API', 'WMS-Sync', 'TMS-Track', 'IoT-Sensors', 'Auth-Service', 'Inventory-API', 'Shipping-Gateway']

// Calcul du niveau de menace basé sur la catégorie
function getThreatLevel(category: AttackCategory): ThreatLevel {
  switch (category) {
    case 'Worms':
    case 'Backdoors':
    case 'Shellcode':
      return 'critical'
    case 'Exploit':
    case 'DoS':
      return 'high'
    case 'Fuzzers':
    case 'Reconnaissance':
      return 'medium'
    case 'Generic':
    case 'Analysis':
      return 'low'
    default:
      return 'low'
  }
}

// Génération d'un flux réseau simulé
export function generateNetworkFlow(): NetworkFlow {
  const category = selectAttackCategory()
  const isAttack = category !== 'Normal'
  
  // Paramètres basés sur le type d'attaque
  let dur = Math.random() * 10
  let sbytes = Math.floor(Math.random() * 10000)
  let dbytes = Math.floor(Math.random() * 10000)
  let sload = Math.random() * 1000
  let spkts = Math.floor(Math.random() * 100)
  
  // Ajuster les paramètres selon le type d'attaque
  if (category === 'DoS') {
    sbytes = Math.floor(Math.random() * 100000) + 50000
    sload = Math.random() * 10000 + 5000
    spkts = Math.floor(Math.random() * 1000) + 500
    dur = Math.random() * 0.5
  } else if (category === 'Reconnaissance') {
    dur = Math.random() * 0.01
    spkts = Math.floor(Math.random() * 50) + 20
    sbytes = Math.floor(Math.random() * 500)
  } else if (category === 'Exploit') {
    sbytes = Math.floor(Math.random() * 5000) + 2000
  }
  
  const riskScore = isAttack 
    ? 50 + Math.random() * 50 
    : Math.random() * 30

  return {
    id: generateId(),
    timestamp: new Date(),
    srcip: generateIP(Math.random() > 0.3),
    dstip: generateIP(true),
    sport: Math.floor(Math.random() * 65535),
    dsport: [80, 443, 8080, 3306, 5432, 6379][Math.floor(Math.random() * 6)],
    proto: ['tcp', 'udp', 'http', 'https'][Math.floor(Math.random() * 4)],
    dur,
    sbytes,
    dbytes,
    sttl: Math.floor(Math.random() * 255),
    dttl: Math.floor(Math.random() * 255),
    sload,
    dload: Math.random() * 1000,
    spkts,
    dpkts: Math.floor(Math.random() * 100),
    service: services[Math.floor(Math.random() * services.length)],
    state: ['FIN', 'CON', 'INT', 'REQ', 'RST'][Math.floor(Math.random() * 5)],
    ct_dst_src_ltm: Math.floor(Math.random() * 50),
    attack_cat: category,
    label: isAttack ? 1 : 0,
    riskScore,
  }
}

// Descriptions des attaques
const attackDescriptions: Record<AttackCategory, string> = {
  Normal: 'Trafic légitime',
  DoS: 'Tentative de saturation des ressources de l\'API de suivi logistique',
  Exploit: 'Exploitation de vulnérabilités dans le protocole de communication ERP',
  Fuzzers: 'Envoi de données aléatoires pour perturber le service API',
  Reconnaissance: 'Collecte d\'informations sur la structure du réseau logistique',
  Worms: 'Logiciel malveillant tentant de se propager entre systèmes partenaires',
  Backdoors: 'Tentative d\'établissement d\'un accès persistant non autorisé',
  Shellcode: 'Injection de code malveillant via payload réseau',
  Generic: 'Comportement anormal générique détecté',
  Analysis: 'Activité d\'analyse suspecte du réseau',
}

// Recommandations par type d'attaque
const recommendations: Record<AttackCategory, string> = {
  Normal: 'Aucune action requise',
  DoS: 'Activer le rate limiting sur l\'IP source. Vérifier les règles de pare-feu. Notifier l\'équipe NOC.',
  Exploit: 'Isoler le système cible. Vérifier les patches de sécurité. Auditer les accès récents.',
  Fuzzers: 'Renforcer la validation des entrées. Activer le WAF. Surveiller les logs d\'erreurs.',
  Reconnaissance: 'Bannissement temporaire (30 min) de l\'IP source. Examiner les journaux d\'accès.',
  Worms: 'URGENT: Isoler le segment réseau. Scanner tous les systèmes connectés. Activer le mode quarantaine.',
  Backdoors: 'CRITIQUE: Déconnecter immédiatement le système. Analyse forensique requise.',
  Shellcode: 'CRITIQUE: Bloquer l\'IP source. Vérifier l\'intégrité du système cible. Activer l\'analyse mémoire.',
  Generic: 'Surveiller le comportement. Collecter plus de données pour analyse.',
  Analysis: 'Documenter les patterns. Renforcer la surveillance sur les segments concernés.',
}

// Génération des valeurs SHAP pour l'explicabilité
export function generateShapExplanation(flow: NetworkFlow): ShapExplanation[] {
  const explanations: ShapExplanation[] = []
  
  if (flow.attack_cat === 'DoS') {
    explanations.push(
      { feature: 'sload', value: flow.sload, shapValue: 0.35, contribution: 'positive', description: 'Charge source anormalement élevée' },
      { feature: 'sbytes', value: flow.sbytes, shapValue: 0.28, contribution: 'positive', description: 'Volume de données source excessif' },
      { feature: 'spkts', value: flow.spkts, shapValue: 0.22, contribution: 'positive', description: 'Nombre de paquets très élevé' },
      { feature: 'dur', value: flow.dur, shapValue: -0.15, contribution: 'negative', description: 'Durée de connexion très courte' },
    )
  } else if (flow.attack_cat === 'Reconnaissance') {
    explanations.push(
      { feature: 'dur', value: flow.dur, shapValue: 0.40, contribution: 'positive', description: 'Durée typique d\'un scan automatisé' },
      { feature: 'ct_dst_src_ltm', value: flow.ct_dst_src_ltm, shapValue: 0.30, contribution: 'positive', description: 'Connexions répétitives suspectes' },
      { feature: 'spkts', value: flow.spkts, shapValue: 0.20, contribution: 'positive', description: 'Pattern de scan de ports' },
    )
  } else if (flow.attack_cat === 'Exploit') {
    explanations.push(
      { feature: 'sbytes', value: flow.sbytes, shapValue: 0.38, contribution: 'positive', description: 'Payload suspect détecté' },
      { feature: 'sttl', value: flow.sttl, shapValue: 0.25, contribution: 'positive', description: 'TTL inhabituel suggérant spoofing' },
      { feature: 'state', value: 0, shapValue: 0.20, contribution: 'positive', description: 'État de connexion anormal' },
    )
  } else {
    explanations.push(
      { feature: 'sbytes', value: flow.sbytes, shapValue: Math.random() * 0.3, contribution: Math.random() > 0.5 ? 'positive' : 'negative', description: 'Volume de données' },
      { feature: 'dur', value: flow.dur, shapValue: Math.random() * 0.2, contribution: Math.random() > 0.5 ? 'positive' : 'negative', description: 'Durée de transaction' },
      { feature: 'sload', value: flow.sload, shapValue: Math.random() * 0.25, contribution: Math.random() > 0.5 ? 'positive' : 'negative', description: 'Charge réseau' },
    )
  }
  
  return explanations.sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue))
}

// Génération d'une alerte à partir d'un flux
export function generateAlertFromFlow(flow: NetworkFlow): Alert | null {
  if (flow.attack_cat === 'Normal') return null
  
  return {
    id: generateId(),
    flowId: flow.id,
    timestamp: flow.timestamp,
    attackType: flow.attack_cat,
    threatLevel: getThreatLevel(flow.attack_cat),
    srcip: flow.srcip,
    dstip: flow.dstip,
    description: attackDescriptions[flow.attack_cat],
    evidence: generateShapExplanation(flow),
    recommendation: recommendations[flow.attack_cat],
    status: 'pending',
    affectedSystem: flow.service,
  }
}

// Génération des métriques système
export function generateSystemMetrics(): SystemMetrics {
  return {
    totalRequests: Math.floor(Math.random() * 50000) + 100000,
    blockedRequests: Math.floor(Math.random() * 500) + 100,
    allowedRequests: Math.floor(Math.random() * 50000) + 95000,
    avgLatency: Math.random() * 30 + 15,
    modelAccuracy: 98.2 + Math.random() * 1.5,
    falsePositiveRate: 0.5 + Math.random() * 1,
    uptime: 99.9 + Math.random() * 0.09,
    cpuUsage: 20 + Math.random() * 40,
    memoryUsage: 30 + Math.random() * 35,
    activeConnections: Math.floor(Math.random() * 500) + 200,
  }
}

// Génération de l'historique du trafic
export function generateTrafficHistory(hours = 24): TrafficStats[] {
  const stats: TrafficStats[] = []
  const now = new Date()
  
  for (let i = hours; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000)
    const baseTraffic = 800 + Math.random() * 400
    
    stats.push({
      timestamp,
      normal: Math.floor(baseTraffic * 0.85),
      dos: Math.floor(baseTraffic * 0.04 + (Math.random() > 0.9 ? Math.random() * 50 : 0)),
      exploit: Math.floor(baseTraffic * 0.03),
      fuzzers: Math.floor(baseTraffic * 0.02),
      reconnaissance: Math.floor(baseTraffic * 0.04),
      other: Math.floor(baseTraffic * 0.02),
      total: Math.floor(baseTraffic),
    })
  }
  
  return stats
}

// Messages initiaux de l'agent IA
export function getInitialAgentMessages(): AIAgentMessage[] {
  return [
    {
      id: generateId(),
      role: 'system',
      content: 'Agent IA NIDS initialisé. Prêt à analyser les incidents de sécurité et fournir des recommandations stratégiques.',
      timestamp: new Date(),
    },
    {
      id: generateId(),
      role: 'assistant',
      content: 'Bonjour ! Je suis l\'Agent IA du système NIDS. Je peux vous aider à analyser les alertes de sécurité, expliquer les décisions du modèle ML, et fournir des recommandations pour protéger votre infrastructure logistique. Sélectionnez une alerte pour obtenir une analyse détaillée, ou posez-moi une question sur la sécurité de votre réseau.',
      timestamp: new Date(),
    },
  ]
}

// Génération de réponses de l'agent IA
export function generateAIResponse(alert: Alert): string {
  const threatLabels: Record<ThreatLevel, string> = {
    low: '🟢 Faible',
    medium: '🟡 Moyen',
    high: '🟠 Élevé',
    critical: '🔴 Critique',
  }
  
  let response = `## Analyse de l'Incident #${alert.id.slice(0, 8)}\n\n`
  response += `### Nature de l'Attaque\n`
  response += `**Type détecté:** ${alert.attackType}\n`
  response += `**Niveau de menace:** ${threatLabels[alert.threatLevel]}\n`
  response += `**Système affecté:** ${alert.affectedSystem}\n\n`
  
  response += `### Preuves Techniques\n`
  for (const evidence of alert.evidence) {
    const arrow = evidence.contribution === 'positive' ? '↑' : '↓'
    response += `- **${evidence.feature}:** ${evidence.value.toFixed(2)} ${arrow} ${evidence.description}\n`
  }
  
  response += `\n### Recommandations\n`
  response += `${alert.recommendation}\n\n`
  
  if (alert.threatLevel === 'critical' || alert.threatLevel === 'high') {
    response += `### ⚠️ Actions Immédiates Requises\n`
    response += `1. Vérifier les logs d'accès de ${alert.affectedSystem}\n`
    response += `2. Isoler l'adresse IP source ${alert.srcip}\n`
    response += `3. Notifier l'équipe de réponse aux incidents\n`
  }
  
  return response
}
