'use client'

import { 
  Shield, 
  Activity, 
  AlertTriangle, 
  Bot, 
  BarChart3, 
  Settings, 
  Network,
  FileText,
  Power,
  Globe,
  Brain,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SystemStatus, ThreatLevel } from '@/lib/types'

interface SidebarProps {
  activeTab: string
  onTabChange: (tab: string) => void
  systemStatus: SystemStatus
  threatLevel: ThreatLevel
  alertCount: number
  isMonitoring: boolean
  onToggleMonitoring: () => void
}

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { id: 'traffic', label: 'Trafic Réseau', icon: Network },
  { id: 'alerts', label: 'Alertes', icon: AlertTriangle },
  { id: 'monitor', label: 'Endpoints', icon: Globe },
  { id: 'agent', label: 'Agent IA', icon: Bot },
  { id: 'ml', label: 'Intelligence ML', icon: Brain },
  { id: 'reports', label: 'Rapports', icon: FileText },
  { id: 'settings', label: 'Paramètres', icon: Settings },
]

const threatColors: Record<ThreatLevel, string> = {
  low: 'bg-success',
  medium: 'bg-warning',
  high: 'bg-accent',
  critical: 'bg-destructive',
}

const statusColors: Record<SystemStatus, string> = {
  online: 'bg-success',
  offline: 'bg-destructive',
  degraded: 'bg-warning',
}

export function Sidebar({ 
  activeTab, 
  onTabChange, 
  systemStatus, 
  threatLevel, 
  alertCount,
  isMonitoring,
  onToggleMonitoring 
}: SidebarProps) {
  return (
    <aside className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col h-screen">
      {/* Logo */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Shield className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-sidebar-foreground">NIDS</h1>
            <p className="text-xs text-muted-foreground">Cyber-IA Security</p>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="bg-sidebar-accent rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">État du système</span>
            <div className="flex items-center gap-1.5">
              <span className={cn("w-2 h-2 rounded-full", statusColors[systemStatus])} />
              <span className="text-xs capitalize text-sidebar-foreground">
                {systemStatus === 'online' ? 'En ligne' : systemStatus === 'offline' ? 'Hors ligne' : 'Dégradé'}
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Niveau de menace</span>
            <div className="flex items-center gap-1.5">
              <span className={cn("w-2 h-2 rounded-full", threatColors[threatLevel], threatLevel === 'critical' && 'threat-pulse')} />
              <span className="text-xs capitalize text-sidebar-foreground">
                {threatLevel === 'low' ? 'Faible' : threatLevel === 'medium' ? 'Moyen' : threatLevel === 'high' ? 'Élevé' : 'Critique'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = activeTab === item.id
            const showBadge = item.id === 'alerts' && alertCount > 0
            
            return (
              <li key={item.id}>
                <button
                  onClick={() => onTabChange(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                    isActive 
                      ? "bg-sidebar-primary text-sidebar-primary-foreground" 
                      : "text-sidebar-foreground hover:bg-sidebar-accent"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span className="flex-1 text-left">{item.label}</span>
                  {showBadge && (
                    <span className={cn(
                      "min-w-5 h-5 flex items-center justify-center rounded-full text-xs font-medium",
                      threatLevel === 'critical' || threatLevel === 'high'
                        ? "bg-destructive text-destructive-foreground"
                        : "bg-warning text-warning-foreground"
                    )}>
                      {alertCount > 99 ? '99+' : alertCount}
                    </span>
                  )}
                </button>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Monitoring Toggle */}
      <div className="p-4 border-t border-sidebar-border">
        <button
          onClick={onToggleMonitoring}
          className={cn(
            "w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
            isMonitoring 
              ? "bg-success/20 text-success border border-success/30 hover:bg-success/30" 
              : "bg-destructive/20 text-destructive border border-destructive/30 hover:bg-destructive/30"
          )}
        >
          <Power className="h-4 w-4" />
          {isMonitoring ? 'Monitoring Actif' : 'Monitoring Arrêté'}
        </button>
        <div className="mt-3 flex items-center justify-center gap-2">
          <Activity className={cn("h-3 w-3", isMonitoring ? "text-success" : "text-muted-foreground")} />
          <span className="text-xs text-muted-foreground">
            {isMonitoring ? 'Analyse en temps réel' : 'En pause'}
          </span>
        </div>
      </div>
    </aside>
  )
}
