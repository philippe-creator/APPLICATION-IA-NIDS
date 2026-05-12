'use client'

import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'
import { 
  AlertTriangle, 
  ShieldX, 
  ShieldCheck, 
  Search, 
  Bug, 
  Radar,
  Skull,
  Code,
  Eye,
  CheckCircle,
  XCircle,
  Microscope,
  Bot
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Alert, AttackCategory, ThreatLevel } from '@/lib/types'

interface AlertListProps {
  alerts: Alert[]
  selectedAlert: Alert | null
  onSelectAlert: (alert: Alert) => void
  onConfirm: (id: string) => void
  onDismiss: (id: string) => void
  onInvestigate: (id: string) => void
  onAnalyzeWithAI: (alert: Alert) => void
}

const attackIcons: Record<AttackCategory, typeof AlertTriangle> = {
  Normal: ShieldCheck,
  DoS: ShieldX,
  Exploit: Bug,
  Fuzzers: Search,
  Reconnaissance: Radar,
  Worms: Skull,
  Backdoors: Code,
  Shellcode: Code,
  Generic: AlertTriangle,
  Analysis: Eye,
}

const threatColors: Record<ThreatLevel, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-success/10', text: 'text-success', border: 'border-success/30' },
  medium: { bg: 'bg-warning/10', text: 'text-warning', border: 'border-warning/30' },
  high: { bg: 'bg-accent/10', text: 'text-accent', border: 'border-accent/30' },
  critical: { bg: 'bg-destructive/10', text: 'text-destructive', border: 'border-destructive/30' },
}

const statusLabels = {
  pending: { label: 'En attente', color: 'bg-warning/20 text-warning' },
  confirmed: { label: 'Confirmée', color: 'bg-destructive/20 text-destructive' },
  dismissed: { label: 'Rejetée', color: 'bg-muted text-muted-foreground' },
  investigating: { label: 'Investigation', color: 'bg-primary/20 text-primary' },
}

export function AlertList({ 
  alerts, 
  selectedAlert,
  onSelectAlert,
  onConfirm, 
  onDismiss, 
  onInvestigate,
  onAnalyzeWithAI
}: AlertListProps) {
  if (alerts.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center">
        <ShieldCheck className="h-12 w-12 text-success mx-auto mb-4" />
        <h3 className="font-semibold text-card-foreground mb-2">Aucune alerte active</h3>
        <p className="text-sm text-muted-foreground">
          Le système surveille le réseau. Aucune menace détectée pour le moment.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const Icon = attackIcons[alert.attackType] || AlertTriangle
        const colors = threatColors[alert.threatLevel]
        const status = statusLabels[alert.status]
        const isSelected = selectedAlert?.id === alert.id
        
        return (
          <div
            key={alert.id}
            className={cn(
              "bg-card border rounded-xl p-4 transition-all cursor-pointer",
              isSelected ? "border-primary ring-1 ring-primary/30" : "border-border hover:border-primary/30",
              alert.threatLevel === 'critical' && alert.status === 'pending' && "threat-pulse"
            )}
            onClick={() => onSelectAlert(alert)}
          >
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className={cn("p-2.5 rounded-lg shrink-0", colors.bg)}>
                <Icon className={cn("h-5 w-5", colors.text)} />
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="font-semibold text-card-foreground">{alert.attackType}</span>
                  <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", status.color)}>
                    {status.label}
                  </span>
                  <span className={cn(
                    "text-xs px-2 py-0.5 rounded-full font-medium border",
                    colors.bg, colors.text, colors.border
                  )}>
                    {alert.threatLevel === 'low' ? 'Faible' : 
                     alert.threatLevel === 'medium' ? 'Moyen' : 
                     alert.threatLevel === 'high' ? 'Élevé' : 'Critique'}
                  </span>
                </div>
                
                <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                  {alert.description}
                </p>
                
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>Source: <span className="font-mono text-card-foreground">{alert.srcip}</span></span>
                  <span>Cible: <span className="font-mono text-card-foreground">{alert.dstip}</span></span>
                  <span>{formatDistanceToNow(alert.timestamp, { addSuffix: true, locale: fr })}</span>
                </div>
              </div>
            </div>
            
            {/* Actions */}
            {alert.status === 'pending' && (
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
                <button
                  onClick={(e) => { e.stopPropagation(); onConfirm(alert.id) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-destructive/20 text-destructive hover:bg-destructive/30 transition-colors"
                >
                  <CheckCircle className="h-3.5 w-3.5" />
                  Confirmer
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onDismiss(alert.id) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-muted text-muted-foreground hover:bg-muted/80 transition-colors"
                >
                  <XCircle className="h-3.5 w-3.5" />
                  Faux positif
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onInvestigate(alert.id) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
                >
                  <Microscope className="h-3.5 w-3.5" />
                  Investiguer
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onAnalyzeWithAI(alert) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-accent/20 text-accent hover:bg-accent/30 transition-colors ml-auto"
                >
                  <Bot className="h-3.5 w-3.5" />
                  Analyser avec IA
                </button>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
