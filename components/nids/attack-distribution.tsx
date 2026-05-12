'use client'

import { useMemo } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import type { Alert } from '@/lib/types'

interface AttackDistributionProps {
  alerts: Alert[]
}

const COLORS = {
  DoS: 'oklch(0.55 0.25 25)',
  Exploit: 'oklch(0.60 0.18 30)',
  Fuzzers: 'oklch(0.75 0.18 85)',
  Reconnaissance: 'oklch(0.65 0.20 175)',
  Worms: 'oklch(0.55 0.20 320)',
  Backdoors: 'oklch(0.60 0.15 280)',
  Generic: 'oklch(0.65 0.10 260)',
  Shellcode: 'oklch(0.50 0.20 340)',
  Analysis: 'oklch(0.70 0.15 200)',
}

export function AttackDistribution({ alerts }: AttackDistributionProps) {
  const data = useMemo(() => {
    const counts: Record<string, number> = {}
    
    for (const alert of alerts) {
      counts[alert.attackType] = (counts[alert.attackType] || 0) + 1
    }
    
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
  }, [alerts])

  if (data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-4">
        <h3 className="font-semibold text-card-foreground mb-2">Distribution des Attaques</h3>
        <p className="text-sm text-muted-foreground text-center py-8">
          Aucune donnée disponible
        </p>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="mb-4">
        <h3 className="font-semibold text-card-foreground">Distribution des Attaques</h3>
        <p className="text-xs text-muted-foreground">Répartition par catégorie</p>
      </div>
      
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={COLORS[entry.name as keyof typeof COLORS] || 'oklch(0.5 0.1 260)'} 
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'oklch(0.18 0.02 260)',
              border: '1px solid oklch(0.30 0.02 260)',
              borderRadius: '8px',
              color: 'oklch(0.95 0.01 260)',
            }}
            formatter={(value: number) => [`${value} alertes`, '']}
          />
          <Legend 
            formatter={(value) => (
              <span style={{ color: 'oklch(0.95 0.01 260)', fontSize: '12px' }}>{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
      
      {/* Stats */}
      <div className="mt-4 pt-4 border-t border-border">
        <div className="grid grid-cols-2 gap-2 text-xs">
          {data.slice(0, 4).map((item) => (
            <div key={item.name} className="flex items-center justify-between">
              <span className="text-muted-foreground">{item.name}</span>
              <span className="font-medium text-card-foreground">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
