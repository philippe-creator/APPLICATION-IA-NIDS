// Module de Surveillance de Site Web
// Monitoring de disponibilité, performance et sécurité

export interface SiteTarget {
  id: string
  url: string
  name: string
  type: 'api' | 'website' | 'service'
  checkInterval: number // en secondes
  enabled: boolean
  alertThresholds: {
    responseTime: number // ms
    errorRate: number // pourcentage
    downtime: number // secondes consécutives
  }
}

export interface SiteCheckResult {
  id: string
  targetId: string
  timestamp: Date
  status: 'up' | 'down' | 'degraded'
  responseTime: number // ms
  statusCode: number | null
  error: string | null
  headers: Record<string, string>
  sslInfo: {
    valid: boolean
    expiresAt: Date | null
    issuer: string | null
  } | null
  securityHeaders: {
    contentSecurityPolicy: boolean
    xFrameOptions: boolean
    xContentTypeOptions: boolean
    strictTransportSecurity: boolean
    xXssProtection: boolean
  }
}

export interface SiteStats {
  targetId: string
  uptime: number // pourcentage sur 24h
  avgResponseTime: number
  minResponseTime: number
  maxResponseTime: number
  totalChecks: number
  successfulChecks: number
  failedChecks: number
  lastCheck: Date
  statusHistory: Array<{
    timestamp: Date
    status: 'up' | 'down' | 'degraded'
    responseTime: number
  }>
}

export interface SecurityScan {
  id: string
  targetId: string
  timestamp: Date
  score: number // 0-100
  vulnerabilities: Array<{
    severity: 'low' | 'medium' | 'high' | 'critical'
    type: string
    description: string
    recommendation: string
  }>
  headers: {
    score: number
    missing: string[]
    present: string[]
  }
  ssl: {
    score: number
    grade: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F'
    issues: string[]
  }
  cookies: {
    score: number
    issues: string[]
  }
}

// Sites de démonstration pré-configurés
export const DEFAULT_TARGETS: SiteTarget[] = [
  {
    id: 'erp-api',
    url: 'https://api.example-erp.com/health',
    name: 'ERP API Gateway',
    type: 'api',
    checkInterval: 30,
    enabled: true,
    alertThresholds: { responseTime: 500, errorRate: 5, downtime: 60 },
  },
  {
    id: 'wms-sync',
    url: 'https://wms.example-logistics.com/status',
    name: 'WMS Sync Service',
    type: 'service',
    checkInterval: 60,
    enabled: true,
    alertThresholds: { responseTime: 1000, errorRate: 10, downtime: 120 },
  },
  {
    id: 'tms-track',
    url: 'https://tracking.example-transport.com',
    name: 'TMS Tracking Portal',
    type: 'website',
    checkInterval: 60,
    enabled: true,
    alertThresholds: { responseTime: 2000, errorRate: 5, downtime: 180 },
  },
  {
    id: 'iot-gateway',
    url: 'https://iot.example-sensors.com/api/v1/ping',
    name: 'IoT Sensor Gateway',
    type: 'api',
    checkInterval: 15,
    enabled: true,
    alertThresholds: { responseTime: 200, errorRate: 2, downtime: 30 },
  },
  {
    id: 'auth-service',
    url: 'https://auth.example-logistics.com/health',
    name: 'Authentication Service',
    type: 'service',
    checkInterval: 30,
    enabled: true,
    alertThresholds: { responseTime: 300, errorRate: 1, downtime: 30 },
  },
]

// Simuler un check de site
export function simulateSiteCheck(target: SiteTarget): SiteCheckResult {
  // Simuler différents scénarios
  const random = Math.random()
  let status: 'up' | 'down' | 'degraded'
  let responseTime: number
  let statusCode: number | null
  let error: string | null = null
  
  if (random < 0.92) {
    // Site UP - 92% du temps
    status = 'up'
    responseTime = 50 + Math.random() * (target.alertThresholds.responseTime * 0.6)
    statusCode = 200
  } else if (random < 0.97) {
    // Site DEGRADED - 5% du temps
    status = 'degraded'
    responseTime = target.alertThresholds.responseTime * (0.8 + Math.random() * 0.5)
    statusCode = [200, 201, 202, 204][Math.floor(Math.random() * 4)]
  } else {
    // Site DOWN - 3% du temps
    status = 'down'
    responseTime = 0
    statusCode = [500, 502, 503, 504, null][Math.floor(Math.random() * 5)]
    error = [
      'Connection timeout',
      'SSL certificate error',
      'DNS resolution failed',
      'Connection refused',
      'Internal server error',
    ][Math.floor(Math.random() * 5)]
  }
  
  // SSL info simulé
  const sslValid = random < 0.98
  const sslExpiry = new Date()
  sslExpiry.setDate(sslExpiry.getDate() + Math.floor(Math.random() * 365))
  
  return {
    id: generateCheckId(),
    targetId: target.id,
    timestamp: new Date(),
    status,
    responseTime,
    statusCode,
    error,
    headers: {
      'content-type': 'application/json',
      'x-request-id': generateCheckId(),
      'cache-control': 'no-cache',
    },
    sslInfo: {
      valid: sslValid,
      expiresAt: sslExpiry,
      issuer: sslValid ? "Let's Encrypt Authority X3" : null,
    },
    securityHeaders: {
      contentSecurityPolicy: Math.random() > 0.3,
      xFrameOptions: Math.random() > 0.2,
      xContentTypeOptions: Math.random() > 0.2,
      strictTransportSecurity: Math.random() > 0.25,
      xXssProtection: Math.random() > 0.15,
    },
  }
}

// Simuler les statistiques d'un site
export function simulateSiteStats(target: SiteTarget, hours = 24): SiteStats {
  const totalChecks = Math.floor((hours * 3600) / target.checkInterval)
  const failedChecks = Math.floor(totalChecks * (0.01 + Math.random() * 0.04))
  const successfulChecks = totalChecks - failedChecks
  
  const responseTimes: number[] = []
  const statusHistory: SiteStats['statusHistory'] = []
  const now = new Date()
  
  for (let i = 0; i < Math.min(100, totalChecks); i++) {
    const timestamp = new Date(now.getTime() - i * target.checkInterval * 1000)
    const rt = 50 + Math.random() * target.alertThresholds.responseTime * 0.8
    responseTimes.push(rt)
    
    const rand = Math.random()
    let status: 'up' | 'down' | 'degraded' = 'up'
    if (rand > 0.97) status = 'down'
    else if (rand > 0.92) status = 'degraded'
    
    statusHistory.push({ timestamp, status, responseTime: rt })
  }
  
  return {
    targetId: target.id,
    uptime: ((successfulChecks / totalChecks) * 100),
    avgResponseTime: responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length,
    minResponseTime: Math.min(...responseTimes),
    maxResponseTime: Math.max(...responseTimes),
    totalChecks,
    successfulChecks,
    failedChecks,
    lastCheck: now,
    statusHistory: statusHistory.reverse(),
  }
}

// Simuler un scan de sécurité
export function simulateSecurityScan(target: SiteTarget): SecurityScan {
  const vulnerabilities: SecurityScan['vulnerabilities'] = []
  
  // Générer des vulnérabilités aléatoires
  if (Math.random() > 0.7) {
    vulnerabilities.push({
      severity: 'low',
      type: 'Information Disclosure',
      description: 'Server version exposed in HTTP headers',
      recommendation: 'Remove or obfuscate server version headers',
    })
  }
  
  if (Math.random() > 0.85) {
    vulnerabilities.push({
      severity: 'medium',
      type: 'Missing Security Header',
      description: 'Content-Security-Policy header not set',
      recommendation: 'Implement CSP to prevent XSS attacks',
    })
  }
  
  if (Math.random() > 0.95) {
    vulnerabilities.push({
      severity: 'high',
      type: 'Outdated TLS',
      description: 'TLS 1.0/1.1 still enabled',
      recommendation: 'Disable TLS 1.0 and 1.1, use TLS 1.2+ only',
    })
  }
  
  if (Math.random() > 0.98) {
    vulnerabilities.push({
      severity: 'critical',
      type: 'SSL Certificate Issue',
      description: 'SSL certificate expires within 7 days',
      recommendation: 'Renew SSL certificate immediately',
    })
  }
  
  const missingHeaders: string[] = []
  const presentHeaders: string[] = []
  
  const secHeaders = [
    'Content-Security-Policy',
    'X-Frame-Options',
    'X-Content-Type-Options',
    'Strict-Transport-Security',
    'X-XSS-Protection',
    'Referrer-Policy',
    'Permissions-Policy',
  ]
  
  for (const header of secHeaders) {
    if (Math.random() > 0.4) {
      presentHeaders.push(header)
    } else {
      missingHeaders.push(header)
    }
  }
  
  const headerScore = (presentHeaders.length / secHeaders.length) * 100
  const sslScore = 80 + Math.random() * 20
  const cookieScore = 70 + Math.random() * 30
  
  const sslIssues: string[] = []
  if (Math.random() > 0.8) sslIssues.push('Certificate chain incomplete')
  if (Math.random() > 0.9) sslIssues.push('OCSP stapling not enabled')
  
  const cookieIssues: string[] = []
  if (Math.random() > 0.6) cookieIssues.push('Some cookies missing Secure flag')
  if (Math.random() > 0.7) cookieIssues.push('Some cookies missing HttpOnly flag')
  
  const overallScore = Math.round(
    (headerScore * 0.3) + 
    (sslScore * 0.4) + 
    (cookieScore * 0.15) + 
    ((100 - vulnerabilities.length * 15) * 0.15)
  )
  
  let sslGrade: SecurityScan['ssl']['grade'] = 'A'
  if (sslScore >= 95) sslGrade = 'A+'
  else if (sslScore >= 90) sslGrade = 'A'
  else if (sslScore >= 80) sslGrade = 'B'
  else if (sslScore >= 70) sslGrade = 'C'
  else if (sslScore >= 60) sslGrade = 'D'
  else sslGrade = 'F'
  
  return {
    id: generateCheckId(),
    targetId: target.id,
    timestamp: new Date(),
    score: overallScore,
    vulnerabilities,
    headers: {
      score: headerScore,
      missing: missingHeaders,
      present: presentHeaders,
    },
    ssl: {
      score: sslScore,
      grade: sslGrade,
      issues: sslIssues,
    },
    cookies: {
      score: cookieScore,
      issues: cookieIssues,
    },
  }
}

function generateCheckId(): string {
  return Math.random().toString(36).substring(2, 15)
}

// Générer l'historique des vérifications pour un site
export function generateCheckHistory(target: SiteTarget, count = 50): SiteCheckResult[] {
  const history: SiteCheckResult[] = []
  const now = new Date()
  
  for (let i = 0; i < count; i++) {
    const check = simulateSiteCheck(target)
    check.timestamp = new Date(now.getTime() - i * target.checkInterval * 1000)
    history.push(check)
  }
  
  return history.reverse()
}
