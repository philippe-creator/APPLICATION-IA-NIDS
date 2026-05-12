'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Globe, 
  Shield, 
  Activity, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  ExternalLink,
  Lock,
  Zap,
  Server,
} from 'lucide-react'
import { 
  DEFAULT_TARGETS, 
  simulateSiteCheck, 
  simulateSiteStats, 
  simulateSecurityScan,
  type SiteTarget,
  type SiteCheckResult,
  type SiteStats,
  type SecurityScan,
} from '@/lib/site-monitor'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'

interface SiteData {
  target: SiteTarget
  lastCheck: SiteCheckResult
  stats: SiteStats
  security: SecurityScan | null
}

export function SiteMonitorDashboard() {
  const [sites, setSites] = useState<SiteData[]>([])
  const [selectedSite, setSelectedSite] = useState<SiteData | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  
  // Initialiser les données des sites
  useEffect(() => {
    refreshAllSites()
  }, [])
  
  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(refreshAllSites, 30000)
    return () => clearInterval(interval)
  }, [autoRefresh])
  
  const refreshAllSites = () => {
    setIsRefreshing(true)
    const updatedSites = DEFAULT_TARGETS.map(target => ({
      target,
      lastCheck: simulateSiteCheck(target),
      stats: simulateSiteStats(target),
      security: null as SecurityScan | null,
    }))
    setSites(updatedSites)
    if (selectedSite) {
      const updated = updatedSites.find(s => s.target.id === selectedSite.target.id)
      if (updated) setSelectedSite(updated)
    }
    setTimeout(() => setIsRefreshing(false), 500)
  }
  
  const runSecurityScan = (siteData: SiteData) => {
    const scan = simulateSecurityScan(siteData.target)
    const updated = { ...siteData, security: scan }
    setSites(prev => prev.map(s => s.target.id === siteData.target.id ? updated : s))
    setSelectedSite(updated)
  }
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up':
        return <CheckCircle className="h-5 w-5 text-success" />
      case 'down':
        return <XCircle className="h-5 w-5 text-destructive" />
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-warning" />
      default:
        return <Activity className="h-5 w-5 text-muted-foreground" />
    }
  }
  
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'up':
        return <Badge className="bg-success/20 text-success border-success/30">En ligne</Badge>
      case 'down':
        return <Badge className="bg-destructive/20 text-destructive border-destructive/30">Hors ligne</Badge>
      case 'degraded':
        return <Badge className="bg-warning/20 text-warning border-warning/30">Degraded</Badge>
      default:
        return <Badge variant="secondary">Inconnu</Badge>
    }
  }
  
  const overallStats = {
    totalSites: sites.length,
    sitesUp: sites.filter(s => s.lastCheck.status === 'up').length,
    sitesDown: sites.filter(s => s.lastCheck.status === 'down').length,
    sitesDegraded: sites.filter(s => s.lastCheck.status === 'degraded').length,
    avgUptime: sites.length > 0 
      ? sites.reduce((sum, s) => sum + s.stats.uptime, 0) / sites.length 
      : 0,
    avgResponseTime: sites.length > 0
      ? sites.reduce((sum, s) => sum + s.stats.avgResponseTime, 0) / sites.length
      : 0,
  }

  return (
    <div className="space-y-6">
      {/* Header avec stats globales */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-card-foreground">Surveillance des Endpoints</h2>
          <p className="text-sm text-muted-foreground">
            Monitoring temps réel de la Supply Chain Control Tower
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'border-success text-success' : ''}
          >
            <Activity className="h-4 w-4 mr-2" />
            Auto: {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={refreshAllSites}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
        </div>
      </div>
      
      {/* Stats globales */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Services en ligne</p>
                <p className="text-2xl font-bold text-success">{overallStats.sitesUp}/{overallStats.totalSites}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-success/30" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Uptime moyen</p>
                <p className="text-2xl font-bold text-primary">{overallStats.avgUptime.toFixed(2)}%</p>
              </div>
              <Activity className="h-8 w-8 text-primary/30" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Latence moyenne</p>
                <p className="text-2xl font-bold text-chart-3">{overallStats.avgResponseTime.toFixed(0)}ms</p>
              </div>
              <Zap className="h-8 w-8 text-chart-3/30" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Alertes actives</p>
                <p className="text-2xl font-bold text-destructive">
                  {overallStats.sitesDown + overallStats.sitesDegraded}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-destructive/30" />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Liste des sites et détails */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Liste des sites */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="text-sm font-semibold text-card-foreground mb-3">Endpoints surveillés</h3>
          {sites.map(siteData => (
            <Card 
              key={siteData.target.id}
              className={`bg-card border-border cursor-pointer transition-all hover:border-primary/50 ${
                selectedSite?.target.id === siteData.target.id ? 'border-primary ring-1 ring-primary/20' : ''
              }`}
              onClick={() => setSelectedSite(siteData)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {getStatusIcon(siteData.lastCheck.status)}
                    <div>
                      <p className="font-medium text-card-foreground text-sm">{siteData.target.name}</p>
                      <p className="text-xs text-muted-foreground truncate max-w-[180px]">
                        {siteData.target.url}
                      </p>
                    </div>
                  </div>
                  {getStatusBadge(siteData.lastCheck.status)}
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {siteData.lastCheck.responseTime.toFixed(0)}ms
                  </span>
                  <span>{siteData.stats.uptime.toFixed(2)}% uptime</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        
        {/* Détails du site sélectionné */}
        <div className="lg:col-span-2">
          {selectedSite ? (
            <div className="space-y-4">
              {/* Header du site */}
              <Card className="bg-card border-border">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        selectedSite.lastCheck.status === 'up' ? 'bg-success/20' :
                        selectedSite.lastCheck.status === 'down' ? 'bg-destructive/20' : 'bg-warning/20'
                      }`}>
                        {selectedSite.target.type === 'api' ? <Server className="h-5 w-5" /> :
                         selectedSite.target.type === 'service' ? <Activity className="h-5 w-5" /> :
                         <Globe className="h-5 w-5" />}
                      </div>
                      <div>
                        <CardTitle className="text-lg">{selectedSite.target.name}</CardTitle>
                        <CardDescription className="flex items-center gap-2">
                          <a 
                            href={selectedSite.target.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-primary hover:underline flex items-center gap-1"
                          >
                            {selectedSite.target.url}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => runSecurityScan(selectedSite)}
                      >
                        <Shield className="h-4 w-4 mr-2" />
                        Scan Sécurité
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Métriques principales */}
                  <div className="grid grid-cols-4 gap-4">
                    <div className="text-center p-3 rounded-lg bg-muted/30">
                      <p className="text-2xl font-bold text-primary">
                        {selectedSite.stats.uptime.toFixed(2)}%
                      </p>
                      <p className="text-xs text-muted-foreground">Uptime 24h</p>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-muted/30">
                      <p className="text-2xl font-bold text-chart-3">
                        {selectedSite.stats.avgResponseTime.toFixed(0)}ms
                      </p>
                      <p className="text-xs text-muted-foreground">Latence moy.</p>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-muted/30">
                      <p className="text-2xl font-bold text-success">
                        {selectedSite.stats.successfulChecks}
                      </p>
                      <p className="text-xs text-muted-foreground">Checks OK</p>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-muted/30">
                      <p className="text-2xl font-bold text-destructive">
                        {selectedSite.stats.failedChecks}
                      </p>
                      <p className="text-xs text-muted-foreground">Échecs</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              {/* Graphique de latence */}
              <Card className="bg-card border-border">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Historique de latence</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={selectedSite.stats.statusHistory.slice(-30)}>
                        <defs>
                          <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis 
                          dataKey="timestamp" 
                          tickFormatter={(val) => format(new Date(val), 'HH:mm')}
                          stroke="var(--muted-foreground)"
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis 
                          stroke="var(--muted-foreground)"
                          tick={{ fontSize: 10 }}
                          tickFormatter={(val) => `${val}ms`}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: 'var(--card)', 
                            border: '1px solid var(--border)',
                            borderRadius: '8px',
                          }}
                          labelFormatter={(val) => format(new Date(val), 'HH:mm:ss', { locale: fr })}
                          formatter={(value: number) => [`${value.toFixed(0)}ms`, 'Latence']}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="responseTime" 
                          stroke="var(--primary)" 
                          fill="url(#latencyGradient)"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
              
              {/* Résultats du scan de sécurité */}
              {selectedSite.security && (
                <Card className="bg-card border-border">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Shield className="h-4 w-4" />
                        Scan de Sécurité
                      </CardTitle>
                      <Badge className={
                        selectedSite.security.score >= 80 ? 'bg-success/20 text-success' :
                        selectedSite.security.score >= 60 ? 'bg-warning/20 text-warning' :
                        'bg-destructive/20 text-destructive'
                      }>
                        Score: {selectedSite.security.score}/100
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* SSL */}
                    <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                      <div className="flex items-center gap-2">
                        <Lock className="h-4 w-4 text-primary" />
                        <span className="text-sm">SSL/TLS</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">Grade {selectedSite.security.ssl.grade}</Badge>
                        <span className="text-sm text-muted-foreground">
                          {selectedSite.security.ssl.score.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    
                    {/* Headers de sécurité */}
                    <div className="p-3 rounded-lg bg-muted/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">Security Headers</span>
                        <span className="text-sm text-muted-foreground">
                          {selectedSite.security.headers.present.length}/
                          {selectedSite.security.headers.present.length + selectedSite.security.headers.missing.length}
                        </span>
                      </div>
                      <Progress 
                        value={selectedSite.security.headers.score} 
                        className="h-2"
                      />
                      {selectedSite.security.headers.missing.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {selectedSite.security.headers.missing.slice(0, 3).map(h => (
                            <Badge key={h} variant="outline" className="text-xs text-warning">
                              Manquant: {h}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    {/* Vulnérabilités */}
                    {selectedSite.security.vulnerabilities.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-destructive">
                          Vulnérabilités détectées ({selectedSite.security.vulnerabilities.length})
                        </p>
                        {selectedSite.security.vulnerabilities.map((vuln, i) => (
                          <div key={i} className="p-2 rounded border border-border bg-muted/20">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge className={
                                vuln.severity === 'critical' ? 'bg-destructive/20 text-destructive' :
                                vuln.severity === 'high' ? 'bg-accent/20 text-accent' :
                                vuln.severity === 'medium' ? 'bg-warning/20 text-warning' :
                                'bg-muted text-muted-foreground'
                              }>
                                {vuln.severity.toUpperCase()}
                              </Badge>
                              <span className="text-sm font-medium">{vuln.type}</span>
                            </div>
                            <p className="text-xs text-muted-foreground">{vuln.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card className="bg-card border-border h-full flex items-center justify-center">
              <div className="text-center p-8">
                <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="font-semibold text-card-foreground mb-2">Sélectionnez un endpoint</h3>
                <p className="text-sm text-muted-foreground">
                  Cliquez sur un service pour voir ses détails et lancer un scan de sécurité.
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
