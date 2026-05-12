'use client'

import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { 
  X, 
  AlertTriangle, 
  Globe, 
  Server, 
  Clock, 
  Bot,
  CheckCircle,
  XCircle,
  Microscope
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ShapVisualization } from './shap-visualization'
import type { Alert, ThreatLevel } from '@/lib/types'

interface AlertDetailProps {
  alert: Alert
  onClose: () => void
  onConfirm: (id: string) => void
  onDismiss: (id: string) => void
  onInvestigate: (id: string) => void
  onAnalyzeWithAI: (alert: Alert) => void
}

const threatColors: Record<ThreatLevel, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-success/10', text: 'text-success', border: 'border-success/30' },
  medium: { bg: 'bg-warning/10', text: 'text-warning', border: 'border-warning/30' },
  high: { bg: 'bg-accent/10', text: 'text-accent', border: 'border-accent/30' },
  critical: { bg: 'bg-destructive/10', text: 'text-destructive', border: 'border-destructive/30' },
}

const threatLabels: Record<ThreatLevel, string> = {
  low: 'Faible',
  medium: 'Moyen',
  high: 'Élevé',
  critical: 'Critique',
}

export function AlertDetail({ 
  alert, 
  onClose, 
  onConfirm, 
  onDismiss, 
  onInvestigate,
  onAnalyzeWithAI 
}: AlertDetailProps) {
  const colors = threatColors[alert.threatLevel]

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      {/* Header */}
      <div className={cn("p-4 border-b", colors.bg, colors.border)}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg", colors.bg)}>
              <AlertTriangle className={cn("h-5 w-5", colors.text)} />
            </div>
            <div>
              <h3 className="font-semibold text-card-foreground">{alert.attackType}</h3>
              <p className="text-xs text-muted-foreground">ID: {alert.id.slice(0, 12)}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
        
        <div className="flex items-center gap-2 mt-3">
          <span className={cn(
            "px-2 py-1 rounded-full text-xs font-medium border",
            colors.bg, colors.text, colors.border
          )}>
            {threatLabels[alert.threatLevel]}
          </span>
          <span className="px-2 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
            {alert.status === 'pending' ? 'En attente' : 
             alert.status === 'confirmed' ? 'Confirmée' :
             alert.status === 'dismissed' ? 'Rejetée' : 'Investigation'}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Description */}
        <div>
          <h4 className="text-xs font-medium text-muted-foreground mb-1">Description</h4>
          <p className="text-sm text-card-foreground">{alert.description}</p>
        </div>

        {/* Network Info */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-muted/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Globe className="h-3.5 w-3.5 text-destructive" />
              <span className="text-xs text-muted-foreground">Source</span>
            </div>
            <p className="font-mono text-sm text-card-foreground">{alert.srcip}</p>
          </div>
          <div className="bg-muted/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Server className="h-3.5 w-3.5 text-primary" />
              <span className="text-xs text-muted-foreground">Destination</span>
            </div>
            <p className="font-mono text-sm text-card-foreground">{alert.dstip}</p>
          </div>
        </div>

        {/* Time & System */}
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">
              {format(alert.timestamp, 'dd/MM/yyyy HH:mm:ss', { locale: fr })}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Server className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">{alert.affectedSystem}</span>
          </div>
        </div>

        {/* SHAP Visualization */}
        {alert.evidence.length > 0 && (
          <ShapVisualization 
            explanations={alert.evidence} 
            title="Facteurs de Détection (SHAP)"
          />
        )}

        {/* Recommendation */}
        <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
          <h4 className="text-xs font-medium text-primary mb-2">Recommandation</h4>
          <p className="text-sm text-card-foreground">{alert.recommendation}</p>
        </div>
      </div>

      {/* Actions */}
      {alert.status === 'pending' && (
        <div className="p-4 border-t border-border bg-muted/20">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onConfirm(alert.id)}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-lg bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors"
            >
              <CheckCircle className="h-4 w-4" />
              Confirmer
            </button>
            <button
              onClick={() => onDismiss(alert.id)}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-lg bg-muted text-muted-foreground hover:bg-muted/80 transition-colors"
            >
              <XCircle className="h-4 w-4" />
              Faux positif
            </button>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={() => onInvestigate(alert.id)}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
            >
              <Microscope className="h-4 w-4" />
              Investiguer
            </button>
            <button
              onClick={() => onAnalyzeWithAI(alert)}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-lg bg-accent/20 text-accent hover:bg-accent/30 transition-colors"
            >
              <Bot className="h-4 w-4" />
              Analyser avec IA
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
