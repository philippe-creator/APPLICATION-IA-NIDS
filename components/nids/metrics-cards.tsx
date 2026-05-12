'use client'

import { 
  ShieldCheck, 
  ShieldAlert, 
  Timer, 
  Target, 
  Cpu,
  Database,
  Zap,
  TrendingUp
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SystemMetrics } from '@/lib/types'

interface MetricsCardsProps {
  metrics: SystemMetrics
}

export function MetricsCards({ metrics }: MetricsCardsProps) {
  const cards = [
    {
      title: 'Requêtes Totales',
      value: metrics.totalRequests.toLocaleString(),
      icon: Zap,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Menaces Bloquées',
      value: metrics.blockedRequests.toLocaleString(),
      icon: ShieldAlert,
      color: 'text-destructive',
      bgColor: 'bg-destructive/10',
      trend: '+12%',
      trendUp: false,
    },
    {
      title: 'Trafic Autorisé',
      value: metrics.allowedRequests.toLocaleString(),
      icon: ShieldCheck,
      color: 'text-success',
      bgColor: 'bg-success/10',
    },
    {
      title: 'Latence Moyenne',
      value: `${metrics.avgLatency.toFixed(1)}ms`,
      icon: Timer,
      color: metrics.avgLatency < 30 ? 'text-success' : metrics.avgLatency < 50 ? 'text-warning' : 'text-destructive',
      bgColor: metrics.avgLatency < 30 ? 'bg-success/10' : metrics.avgLatency < 50 ? 'bg-warning/10' : 'bg-destructive/10',
    },
    {
      title: 'Précision ML',
      value: `${metrics.modelAccuracy.toFixed(1)}%`,
      icon: Target,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Faux Positifs',
      value: `${metrics.falsePositiveRate.toFixed(2)}%`,
      icon: TrendingUp,
      color: metrics.falsePositiveRate < 1 ? 'text-success' : 'text-warning',
      bgColor: metrics.falsePositiveRate < 1 ? 'bg-success/10' : 'bg-warning/10',
    },
    {
      title: 'CPU',
      value: `${metrics.cpuUsage.toFixed(0)}%`,
      icon: Cpu,
      color: metrics.cpuUsage < 50 ? 'text-success' : metrics.cpuUsage < 80 ? 'text-warning' : 'text-destructive',
      bgColor: metrics.cpuUsage < 50 ? 'bg-success/10' : metrics.cpuUsage < 80 ? 'bg-warning/10' : 'bg-destructive/10',
    },
    {
      title: 'Mémoire',
      value: `${metrics.memoryUsage.toFixed(0)}%`,
      icon: Database,
      color: metrics.memoryUsage < 60 ? 'text-success' : metrics.memoryUsage < 85 ? 'text-warning' : 'text-destructive',
      bgColor: metrics.memoryUsage < 60 ? 'bg-success/10' : metrics.memoryUsage < 85 ? 'bg-warning/10' : 'bg-destructive/10',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon
        return (
          <div
            key={card.title}
            className="bg-card border border-border rounded-xl p-4 transition-all hover:border-primary/30"
          >
            <div className="flex items-start justify-between mb-3">
              <div className={cn("p-2 rounded-lg", card.bgColor)}>
                <Icon className={cn("h-4 w-4", card.color)} />
              </div>
              {card.trend && (
                <span className={cn(
                  "text-xs font-medium px-1.5 py-0.5 rounded",
                  card.trendUp ? "bg-success/20 text-success" : "bg-destructive/20 text-destructive"
                )}>
                  {card.trend}
                </span>
              )}
            </div>
            <p className="text-2xl font-bold text-card-foreground">{card.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{card.title}</p>
          </div>
        )
      })}
    </div>
  )
}
