// Types pour le système NIDS

export type AttackCategory = 
  | 'Normal'
  | 'DoS'
  | 'Exploit'
  | 'Fuzzers'
  | 'Reconnaissance'
  | 'Worms'
  | 'Backdoors'
  | 'Shellcode'
  | 'Generic'
  | 'Analysis'

export type ThreatLevel = 'low' | 'medium' | 'high' | 'critical'

export type SystemStatus = 'online' | 'offline' | 'degraded'

export interface NetworkFlow {
  id: string
  timestamp: Date
  srcip: string
  dstip: string
  sport: number
  dsport: number
  proto: string
  dur: number
  sbytes: number
  dbytes: number
  sttl: number
  dttl: number
  sload: number
  dload: number
  spkts: number
  dpkts: number
  service: string
  state: string
  ct_dst_src_ltm: number
  attack_cat: AttackCategory
  label: 0 | 1 // 0 = normal, 1 = attack
  riskScore: number
}

export interface Alert {
  id: string
  flowId: string
  timestamp: Date
  attackType: AttackCategory
  threatLevel: ThreatLevel
  srcip: string
  dstip: string
  description: string
  evidence: ShapExplanation[]
  recommendation: string
  status: 'pending' | 'confirmed' | 'dismissed' | 'investigating'
  affectedSystem: string
}

export interface ShapExplanation {
  feature: string
  value: number
  shapValue: number
  contribution: 'positive' | 'negative'
  description: string
}

export interface ModelPrediction {
  prediction: AttackCategory
  confidence: number
  isAnomaly: boolean
  reconstructionError?: number
  shapValues: ShapExplanation[]
  ensembleVotes: {
    lightgbm: AttackCategory
    xgboost: AttackCategory
    randomforest: AttackCategory
  }
}

export interface SystemMetrics {
  totalRequests: number
  blockedRequests: number
  allowedRequests: number
  avgLatency: number
  modelAccuracy: number
  falsePositiveRate: number
  uptime: number
  cpuUsage: number
  memoryUsage: number
  activeConnections: number
}

export interface TrafficStats {
  timestamp: Date
  normal: number
  dos: number
  exploit: number
  fuzzers: number
  reconnaissance: number
  other: number
  total: number
}

export interface IncidentReport {
  id: string
  alertId: string
  createdAt: Date
  title: string
  summary: string
  businessImpact: string
  technicalEvidence: string[]
  actionsTaken: string[]
  recommendations: string[]
  status: 'draft' | 'final'
}

export interface AIAgentMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  alertContext?: Alert
}

export interface DashboardState {
  systemStatus: SystemStatus
  metrics: SystemMetrics
  recentAlerts: Alert[]
  trafficHistory: TrafficStats[]
  activeThreatLevel: ThreatLevel
}
