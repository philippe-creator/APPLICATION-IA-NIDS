'use client'

import { useState, useEffect } from 'react'
import { useNIDS } from '@/hooks/use-nids'
import { Sidebar } from '@/components/nids/sidebar'
import { MetricsCards } from '@/components/nids/metrics-cards'
import { TrafficChart } from '@/components/nids/traffic-chart'
import { AlertList } from '@/components/nids/alert-list'
import { AlertDetail } from '@/components/nids/alert-detail'
import { AIAgent } from '@/components/nids/ai-agent'
import { NetworkFlowTable } from '@/components/nids/network-flow-table'
import { AttackDistribution } from '@/components/nids/attack-distribution'
import { ModelPerformance } from '@/components/nids/model-performance'
import { ReportGenerator } from '@/components/nids/report-generator'
import { SettingsPanel } from '@/components/nids/settings-panel'
import { SiteMonitorDashboard } from '@/components/nids/site-monitor-dashboard'
import { MLInsights } from '@/components/nids/ml-insights'
import { Activity, Shield, Clock, Zap, Server, Globe, Brain } from 'lucide-react'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { Badge } from '@/components/ui/badge'

export default function NIDSDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [currentTime, setCurrentTime] = useState<Date | null>(null)
  
  // Hydration-safe date handling
  useEffect(() => {
    setCurrentTime(new Date())
    const interval = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(interval)
  }, [])
  
  const {
    systemStatus,
    metrics,
    alerts,
    trafficHistory,
    recentFlows,
    agentMessages,
    selectedAlert,
    isMonitoring,
    activeThreatLevel,
    confirmAlert,
    dismissAlert,
    investigateAlert,
    analyzeWithAI,
    sendAgentMessage,
    toggleMonitoring,
    setSelectedAlert,
  } = useNIDS()

  const pendingAlerts = alerts.filter(a => a.status === 'pending')

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            {/* Metrics */}
            <MetricsCards metrics={metrics} />
            
            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <TrafficChart data={trafficHistory} />
              </div>
              <div>
                <AttackDistribution alerts={alerts} />
              </div>
            </div>
            
            {/* Recent Alerts & Model Performance */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <div className="bg-card border border-border rounded-xl p-4 mb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-card-foreground">Alertes Recentes</h3>
                    <span className="text-xs text-muted-foreground">
                      {pendingAlerts.length} en attente
                    </span>
                  </div>
                  <AlertList
                    alerts={alerts.slice(0, 5)}
                    selectedAlert={selectedAlert}
                    onSelectAlert={setSelectedAlert}
                    onConfirm={confirmAlert}
                    onDismiss={dismissAlert}
                    onInvestigate={investigateAlert}
                    onAnalyzeWithAI={analyzeWithAI}
                  />
                </div>
              </div>
              <div>
                <ModelPerformance 
                  accuracy={metrics.modelAccuracy} 
                  falsePositiveRate={metrics.falsePositiveRate} 
                />
              </div>
            </div>
          </div>
        )

      case 'traffic':
        return (
          <div className="space-y-6">
            <TrafficChart data={trafficHistory} height={400} />
            <NetworkFlowTable flows={recentFlows} maxItems={30} />
          </div>
        )

      case 'alerts':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="bg-card border border-border rounded-xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-card-foreground">Toutes les Alertes</h3>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-2 py-1 rounded-full bg-warning/20 text-warning">
                      {pendingAlerts.length} en attente
                    </span>
                    <span className="px-2 py-1 rounded-full bg-destructive/20 text-destructive">
                      {alerts.filter(a => a.status === 'confirmed').length} confirmees
                    </span>
                  </div>
                </div>
                <AlertList
                  alerts={alerts}
                  selectedAlert={selectedAlert}
                  onSelectAlert={setSelectedAlert}
                  onConfirm={confirmAlert}
                  onDismiss={dismissAlert}
                  onInvestigate={investigateAlert}
                  onAnalyzeWithAI={analyzeWithAI}
                />
              </div>
            </div>
            <div>
              {selectedAlert ? (
                <AlertDetail
                  alert={selectedAlert}
                  onClose={() => setSelectedAlert(null)}
                  onConfirm={confirmAlert}
                  onDismiss={dismissAlert}
                  onInvestigate={investigateAlert}
                  onAnalyzeWithAI={analyzeWithAI}
                />
              ) : (
                <div className="bg-card border border-border rounded-xl p-8 text-center">
                  <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-semibold text-card-foreground mb-2">Selectionnez une alerte</h3>
                  <p className="text-sm text-muted-foreground">
                    Cliquez sur une alerte pour voir les details et l&apos;explicabilite SHAP.
                  </p>
                </div>
              )}
            </div>
          </div>
        )

      case 'agent':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AIAgent
                messages={agentMessages}
                onSendMessage={sendAgentMessage}
                selectedAlert={selectedAlert}
              />
            </div>
            <div>
              <div className="bg-card border border-border rounded-xl p-4 mb-4">
                <h3 className="font-semibold text-card-foreground mb-4">Alertes pour Analyse</h3>
                {pendingAlerts.length > 0 ? (
                  <div className="space-y-2">
                    {pendingAlerts.slice(0, 5).map((alert) => (
                      <button
                        key={alert.id}
                        onClick={() => analyzeWithAI(alert)}
                        className="w-full text-left p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-card-foreground">
                            {alert.attackType}
                          </span>
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            alert.threatLevel === 'critical' ? 'bg-destructive/20 text-destructive' :
                            alert.threatLevel === 'high' ? 'bg-accent/20 text-accent' :
                            'bg-warning/20 text-warning'
                          }`}>
                            {alert.threatLevel}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground truncate">
                          {alert.srcip} → {alert.dstip}
                        </p>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    Aucune alerte en attente
                  </p>
                )}
              </div>
              <AttackDistribution alerts={alerts} />
            </div>
          </div>
        )

      case 'monitor':
        return <SiteMonitorDashboard />

      case 'ml':
        return <MLInsights />

      case 'reports':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ReportGenerator alerts={alerts} metrics={metrics} />
            <div className="space-y-4">
              <ModelPerformance 
                accuracy={metrics.modelAccuracy} 
                falsePositiveRate={metrics.falsePositiveRate} 
              />
            </div>
          </div>
        )

      case 'settings':
        return (
          <div className="max-w-2xl">
            <SettingsPanel />
          </div>
        )

      default:
        return null
    }
  }

  const getThreatBadge = () => {
    switch (activeThreatLevel) {
      case 'critical':
        return <Badge className="bg-destructive/20 text-destructive border-destructive/30 animate-pulse">CRITIQUE</Badge>
      case 'high':
        return <Badge className="bg-accent/20 text-accent border-accent/30">ELEVE</Badge>
      case 'medium':
        return <Badge className="bg-warning/20 text-warning border-warning/30">MOYEN</Badge>
      default:
        return <Badge className="bg-success/20 text-success border-success/30">FAIBLE</Badge>
    }
  }

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        systemStatus={systemStatus}
        threatLevel={activeThreatLevel}
        alertCount={pendingAlerts.length}
        isMonitoring={isMonitoring}
        onToggleMonitoring={toggleMonitoring}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-foreground flex items-center gap-3">
                {activeTab === 'dashboard' && (
                  <>
                    <Zap className="h-5 w-5 text-primary" />
                    Dashboard NIDS
                  </>
                )}
                {activeTab === 'traffic' && (
                  <>
                    <Activity className="h-5 w-5 text-chart-5" />
                    Analyse du Trafic
                  </>
                )}
                {activeTab === 'alerts' && (
                  <>
                    <Shield className="h-5 w-5 text-destructive" />
                    Gestion des Alertes
                  </>
                )}
                {activeTab === 'agent' && (
                  <>
                    <Brain className="h-5 w-5 text-chart-4" />
                    Agent IA
                  </>
                )}
                {activeTab === 'monitor' && (
                  <>
                    <Globe className="h-5 w-5 text-primary" />
                    Surveillance Endpoints
                  </>
                )}
                {activeTab === 'ml' && (
                  <>
                    <Server className="h-5 w-5 text-chart-3" />
                    Intelligence ML
                  </>
                )}
                {activeTab === 'reports' && (
                  <>
                    <Activity className="h-5 w-5 text-warning" />
                    Rapports de Securite
                  </>
                )}
                {activeTab === 'settings' && (
                  <>
                    <Server className="h-5 w-5 text-muted-foreground" />
                    Configuration
                  </>
                )}
              </h1>
              <p className="text-sm text-muted-foreground">
                Supply Chain Control Tower - Protection Logistique Industrielle
              </p>
            </div>
            <div className="flex items-center gap-4">
              {/* Niveau de menace */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Niveau:</span>
                {getThreatBadge()}
              </div>
              
              {/* Heure */}
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">
                  {currentTime ? format(currentTime, 'EEEE dd MMMM yyyy, HH:mm', { locale: fr }) : '--'}
                </span>
              </div>
              
              {/* Connexions actives */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted">
                <Activity className={`h-4 w-4 ${isMonitoring ? 'text-success' : 'text-muted-foreground'}`} />
                <span className="text-sm text-card-foreground">
                  {metrics.activeConnections} connexions
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-6">
          {renderContent()}
        </div>
      </main>
    </div>
  )
}
