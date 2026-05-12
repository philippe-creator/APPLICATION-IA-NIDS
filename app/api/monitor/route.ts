import { NextRequest, NextResponse } from 'next/server'
import { 
  DEFAULT_TARGETS, 
  simulateSiteCheck, 
  simulateSiteStats,
  simulateSecurityScan,
  generateCheckHistory,
  type SiteTarget,
} from '@/lib/site-monitor'

// API de surveillance de sites web
// Endpoint: POST /api/monitor - Effectuer un check
// Endpoint: GET /api/monitor - Obtenir le status de tous les sites

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const action = searchParams.get('action')
  const targetId = searchParams.get('targetId')
  
  try {
    switch (action) {
      case 'stats':
        // Obtenir les statistiques d'un site
        if (targetId) {
          const target = DEFAULT_TARGETS.find(t => t.id === targetId)
          if (!target) {
            return NextResponse.json({ error: 'Target not found' }, { status: 404 })
          }
          return NextResponse.json({
            success: true,
            stats: simulateSiteStats(target),
          })
        }
        // Stats pour tous les sites
        return NextResponse.json({
          success: true,
          stats: DEFAULT_TARGETS.map(t => simulateSiteStats(t)),
        })
        
      case 'security':
        // Scan de sécurité
        if (targetId) {
          const target = DEFAULT_TARGETS.find(t => t.id === targetId)
          if (!target) {
            return NextResponse.json({ error: 'Target not found' }, { status: 404 })
          }
          return NextResponse.json({
            success: true,
            scan: simulateSecurityScan(target),
          })
        }
        return NextResponse.json({
          success: true,
          scans: DEFAULT_TARGETS.map(t => simulateSecurityScan(t)),
        })
        
      case 'history':
        // Historique des checks
        if (targetId) {
          const target = DEFAULT_TARGETS.find(t => t.id === targetId)
          if (!target) {
            return NextResponse.json({ error: 'Target not found' }, { status: 404 })
          }
          return NextResponse.json({
            success: true,
            history: generateCheckHistory(target),
          })
        }
        return NextResponse.json({ error: 'targetId required for history' }, { status: 400 })
        
      default:
        // Status de tous les sites
        return NextResponse.json({
          success: true,
          targets: DEFAULT_TARGETS,
          status: DEFAULT_TARGETS.map(target => ({
            target,
            lastCheck: simulateSiteCheck(target),
            stats: {
              uptime: 99.5 + Math.random() * 0.4,
              avgResponseTime: 50 + Math.random() * 200,
            },
          })),
          timestamp: new Date().toISOString(),
        })
    }
  } catch (error) {
    console.error('[Site Monitor API] Error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: String(error) },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, targetId, url } = body as { 
      action: string
      targetId?: string
      url?: string 
    }
    
    switch (action) {
      case 'check':
        // Effectuer un check immédiat
        if (targetId) {
          const target = DEFAULT_TARGETS.find(t => t.id === targetId)
          if (!target) {
            return NextResponse.json({ error: 'Target not found' }, { status: 404 })
          }
          return NextResponse.json({
            success: true,
            result: simulateSiteCheck(target),
          })
        }
        
        // Check d'une URL personnalisée
        if (url) {
          const customTarget: SiteTarget = {
            id: 'custom-' + Date.now(),
            url,
            name: 'Custom Check',
            type: 'website',
            checkInterval: 60,
            enabled: true,
            alertThresholds: { responseTime: 2000, errorRate: 5, downtime: 120 },
          }
          return NextResponse.json({
            success: true,
            result: simulateSiteCheck(customTarget),
          })
        }
        
        return NextResponse.json({ error: 'targetId or url required' }, { status: 400 })
        
      case 'scan':
        // Scan de sécurité
        if (targetId) {
          const target = DEFAULT_TARGETS.find(t => t.id === targetId)
          if (!target) {
            return NextResponse.json({ error: 'Target not found' }, { status: 404 })
          }
          return NextResponse.json({
            success: true,
            scan: simulateSecurityScan(target),
          })
        }
        return NextResponse.json({ error: 'targetId required' }, { status: 400 })
        
      case 'checkAll':
        // Check tous les sites
        return NextResponse.json({
          success: true,
          results: DEFAULT_TARGETS.map(target => ({
            targetId: target.id,
            check: simulateSiteCheck(target),
          })),
          timestamp: new Date().toISOString(),
        })
        
      default:
        return NextResponse.json(
          { error: 'Invalid action', valid: ['check', 'scan', 'checkAll'] },
          { status: 400 }
        )
    }
  } catch (error) {
    console.error('[Site Monitor API] Error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: String(error) },
      { status: 500 }
    )
  }
}
