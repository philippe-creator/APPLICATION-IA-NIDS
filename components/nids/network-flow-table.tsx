'use client'

import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'
import { ShieldCheck, ShieldAlert, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { NetworkFlow } from '@/lib/types'

interface NetworkFlowTableProps {
  flows: NetworkFlow[]
  maxItems?: number
}

export function NetworkFlowTable({ flows, maxItems = 20 }: NetworkFlowTableProps) {
  const displayedFlows = flows.slice(0, maxItems)

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold text-card-foreground">Flux Réseau en Temps Réel</h3>
        <p className="text-xs text-muted-foreground">Dernières connexions analysées par le moteur ML</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Temps</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Source</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Destination</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Proto</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Service</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Données</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Classification</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {displayedFlows.map((flow) => (
              <tr 
                key={flow.id} 
                className={cn(
                  "transition-colors",
                  flow.label === 1 ? "bg-destructive/5 hover:bg-destructive/10" : "hover:bg-muted/30"
                )}
              >
                <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                  {formatDistanceToNow(flow.timestamp, { addSuffix: true, locale: fr })}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <span className="font-mono text-xs text-card-foreground">{flow.srcip}</span>
                    <span className="text-muted-foreground">:{flow.sport}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <span className="font-mono text-xs text-card-foreground">{flow.dstip}</span>
                    <span className="text-muted-foreground">:{flow.dsport}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-muted text-muted-foreground uppercase">
                    {flow.proto}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{flow.service}</td>
                <td className="px-4 py-3">
                  <span className="text-xs text-card-foreground">
                    {(flow.sbytes / 1024).toFixed(1)} KB
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5">
                    {flow.label === 0 ? (
                      <ShieldCheck className="h-3.5 w-3.5 text-success" />
                    ) : (
                      <ShieldAlert className="h-3.5 w-3.5 text-destructive" />
                    )}
                    <span className={cn(
                      "text-xs font-medium",
                      flow.label === 0 ? "text-success" : "text-destructive"
                    )}>
                      {flow.attack_cat}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div 
                        className={cn(
                          "h-full rounded-full",
                          flow.riskScore < 30 ? "bg-success" :
                          flow.riskScore < 60 ? "bg-warning" : "bg-destructive"
                        )}
                        style={{ width: `${flow.riskScore}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-8">
                      {flow.riskScore.toFixed(0)}%
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {flows.length > maxItems && (
        <div className="p-3 border-t border-border text-center">
          <span className="text-xs text-muted-foreground">
            Affichage de {maxItems} sur {flows.length} flux
          </span>
        </div>
      )}
    </div>
  )
}
