'use client'

import { useMemo } from 'react'
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import type { TrafficStats } from '@/lib/types'

interface TrafficChartProps {
  data: TrafficStats[]
  showLegend?: boolean
  height?: number
}

export function TrafficChart({ data, showLegend = true, height = 300 }: TrafficChartProps) {
  const chartData = useMemo(() => {
    return data.map(item => ({
      time: format(item.timestamp, 'HH:mm', { locale: fr }),
      Normal: item.normal,
      DoS: item.dos,
      Exploit: item.exploit,
      Reconnaissance: item.reconnaissance,
      Autres: item.fuzzers + item.other,
    }))
  }, [data])

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-card-foreground">Trafic Réseau</h3>
          <p className="text-xs text-muted-foreground">Distribution du trafic sur les dernières 24h</p>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorNormal" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="oklch(0.65 0.20 175)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="oklch(0.65 0.20 175)" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorDoS" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="oklch(0.55 0.25 25)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="oklch(0.55 0.25 25)" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorExploit" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="oklch(0.60 0.18 30)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="oklch(0.60 0.18 30)" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorRecon" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="oklch(0.75 0.18 85)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="oklch(0.75 0.18 85)" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.30 0.02 260)" vertical={false} />
          <XAxis 
            dataKey="time" 
            tick={{ fill: 'oklch(0.65 0.01 260)', fontSize: 11 }}
            axisLine={{ stroke: 'oklch(0.30 0.02 260)' }}
            tickLine={false}
          />
          <YAxis 
            tick={{ fill: 'oklch(0.65 0.01 260)', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'oklch(0.18 0.02 260)',
              border: '1px solid oklch(0.30 0.02 260)',
              borderRadius: '8px',
              color: 'oklch(0.95 0.01 260)',
            }}
            labelStyle={{ color: 'oklch(0.65 0.01 260)' }}
          />
          {showLegend && (
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              formatter={(value) => <span style={{ color: 'oklch(0.95 0.01 260)', fontSize: '12px' }}>{value}</span>}
            />
          )}
          <Area
            type="monotone"
            dataKey="Normal"
            stackId="1"
            stroke="oklch(0.65 0.20 175)"
            fill="url(#colorNormal)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="DoS"
            stackId="2"
            stroke="oklch(0.55 0.25 25)"
            fill="url(#colorDoS)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="Exploit"
            stackId="3"
            stroke="oklch(0.60 0.18 30)"
            fill="url(#colorExploit)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="Reconnaissance"
            stackId="4"
            stroke="oklch(0.75 0.18 85)"
            fill="url(#colorRecon)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
