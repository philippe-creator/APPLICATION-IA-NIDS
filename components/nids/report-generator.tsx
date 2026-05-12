'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { FileText, Download, Calendar, Shield, AlertTriangle, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Alert, SystemMetrics } from '@/lib/types'

interface ReportGeneratorProps {
  alerts: Alert[]
  metrics: SystemMetrics
}

export function ReportGenerator({ alerts, metrics }: ReportGeneratorProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<'24h' | '7d' | '30d'>('24h')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedReport, setGeneratedReport] = useState<string | null>(null)

  const periods = [
    { id: '24h', label: 'Dernières 24h' },
    { id: '7d', label: '7 derniers jours' },
    { id: '30d', label: '30 derniers jours' },
  ]

  const generateReport = async () => {
    setIsGenerating(true)
    
    // Simuler la génération
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const confirmedAlerts = alerts.filter(a => a.status === 'confirmed')
    const pendingAlerts = alerts.filter(a => a.status === 'pending')
    const dismissedAlerts = alerts.filter(a => a.status === 'dismissed')
    
    const criticalAlerts = alerts.filter(a => a.threatLevel === 'critical')
    const highAlerts = alerts.filter(a => a.threatLevel === 'high')
    
    const attackTypes: Record<string, number> = {}
    for (const alert of alerts) {
      attackTypes[alert.attackType] = (attackTypes[alert.attackType] || 0) + 1
    }
    
    const topAttacks = Object.entries(attackTypes)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
    
    const report = `
# Rapport de Sécurité NIDS
## Période: ${selectedPeriod === '24h' ? 'Dernières 24 heures' : selectedPeriod === '7d' ? '7 derniers jours' : '30 derniers jours'}
### Généré le ${format(new Date(), 'dd MMMM yyyy à HH:mm', { locale: fr })}

---

## Résumé Exécutif

Ce rapport présente une analyse des incidents de sécurité détectés par le système NIDS (Network Intrusion Detection System) intelligent pour la plateforme logistique.

### Métriques Clés
- **Requêtes totales analysées:** ${metrics.totalRequests.toLocaleString()}
- **Menaces bloquées:** ${metrics.blockedRequests}
- **Trafic autorisé:** ${metrics.allowedRequests.toLocaleString()}
- **Précision du modèle ML:** ${metrics.modelAccuracy.toFixed(1)}%
- **Taux de faux positifs:** ${metrics.falsePositiveRate.toFixed(2)}%

---

## État des Alertes

| Statut | Nombre |
|--------|--------|
| En attente | ${pendingAlerts.length} |
| Confirmées | ${confirmedAlerts.length} |
| Rejetées (FP) | ${dismissedAlerts.length} |
| **Total** | **${alerts.length}** |

### Par Niveau de Menace
- 🔴 **Critiques:** ${criticalAlerts.length}
- 🟠 **Élevées:** ${highAlerts.length}
- 🟡 **Moyennes:** ${alerts.filter(a => a.threatLevel === 'medium').length}
- 🟢 **Faibles:** ${alerts.filter(a => a.threatLevel === 'low').length}

---

## Types d'Attaques Détectées

${topAttacks.map(([type, count], index) => `${index + 1}. **${type}**: ${count} incidents`).join('\n')}

---

## Recommandations

${criticalAlerts.length > 0 ? '⚠️ **URGENT:** Des alertes critiques nécessitent une attention immédiate.\n' : ''}
1. Continuer la surveillance active du réseau
2. Examiner les alertes en attente de validation
3. Mettre à jour les règles de pare-feu si nécessaire
4. Former les équipes sur les nouvelles menaces détectées
5. Planifier un audit de sécurité si le taux d'incidents augmente

---

## Performance du Système

- **Latence moyenne d'analyse:** ${metrics.avgLatency.toFixed(1)}ms
- **Uptime du système:** ${metrics.uptime.toFixed(2)}%
- **Utilisation CPU:** ${metrics.cpuUsage.toFixed(0)}%
- **Utilisation mémoire:** ${metrics.memoryUsage.toFixed(0)}%

---

*Rapport généré automatiquement par NIDS Cyber-IA*
*Pour toute question, contactez l'équipe de sécurité*
`
    
    setGeneratedReport(report)
    setIsGenerating(false)
  }

  const downloadReport = () => {
    if (!generatedReport) return
    
    const blob = new Blob([generatedReport], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rapport-nids-${format(new Date(), 'yyyy-MM-dd')}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Stats rapides
  const confirmedCount = alerts.filter(a => a.status === 'confirmed').length
  const pendingCount = alerts.filter(a => a.status === 'pending').length
  const criticalCount = alerts.filter(a => a.threatLevel === 'critical').length

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-primary/10 rounded-lg">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-card-foreground">Générateur de Rapports</h3>
            <p className="text-xs text-muted-foreground">Créez des rapports d&apos;incidents détaillés</p>
          </div>
        </div>

        {/* Period Selection */}
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Période:</span>
          <div className="flex gap-1">
            {periods.map((period) => (
              <button
                key={period.id}
                onClick={() => setSelectedPeriod(period.id as '24h' | '7d' | '30d')}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-lg transition-colors",
                  selectedPeriod === period.id
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                )}
              >
                {period.label}
              </button>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="p-3 bg-muted/30 rounded-lg text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <AlertTriangle className="h-4 w-4 text-warning" />
            </div>
            <p className="text-xl font-bold text-card-foreground">{pendingCount}</p>
            <p className="text-xs text-muted-foreground">En attente</p>
          </div>
          <div className="p-3 bg-muted/30 rounded-lg text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Shield className="h-4 w-4 text-destructive" />
            </div>
            <p className="text-xl font-bold text-card-foreground">{confirmedCount}</p>
            <p className="text-xs text-muted-foreground">Confirmées</p>
          </div>
          <div className="p-3 bg-muted/30 rounded-lg text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <CheckCircle className="h-4 w-4 text-success" />
            </div>
            <p className="text-xl font-bold text-card-foreground">{criticalCount}</p>
            <p className="text-xs text-muted-foreground">Critiques</p>
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={generateReport}
          disabled={isGenerating}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {isGenerating ? (
            <>
              <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              Génération en cours...
            </>
          ) : (
            <>
              <FileText className="h-4 w-4" />
              Générer le rapport
            </>
          )}
        </button>
      </div>

      {/* Generated Report Preview */}
      {generatedReport && (
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-card-foreground">Aperçu du rapport</h4>
            <button
              onClick={downloadReport}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-success/20 text-success hover:bg-success/30 transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              Télécharger (.md)
            </button>
          </div>
          
          <div className="max-h-96 overflow-y-auto bg-muted/30 rounded-lg p-4">
            <pre className="text-xs text-card-foreground whitespace-pre-wrap font-mono">
              {generatedReport}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
