'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Brain, Zap, Target, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ModelPerformanceProps {
  accuracy: number
  falsePositiveRate: number
}

export function ModelPerformance({ accuracy, falsePositiveRate }: ModelPerformanceProps) {
  // Données simulées pour les métriques par classe
  const classMetrics = [
    { name: 'Normal', precision: 99.2, recall: 98.8, f1: 99.0 },
    { name: 'DoS', precision: 98.5, recall: 99.1, f1: 98.8 },
    { name: 'Exploit', precision: 96.2, recall: 95.8, f1: 96.0 },
    { name: 'Recon', precision: 97.8, recall: 96.5, f1: 97.1 },
    { name: 'Fuzzers', precision: 94.5, recall: 93.2, f1: 93.8 },
  ]

  // Votes des modèles de l'ensemble
  const ensembleVotes = [
    { name: 'LightGBM', confidence: 98.2, color: 'oklch(0.65 0.20 175)' },
    { name: 'XGBoost', confidence: 97.8, color: 'oklch(0.60 0.18 30)' },
    { name: 'RandomForest', confidence: 96.5, color: 'oklch(0.75 0.18 85)' },
  ]

  return (
    <div className="space-y-4">
      {/* Global Metrics */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-card-foreground">Performance du Modèle ML</h3>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-primary mb-1">
              <Target className="h-4 w-4" />
              <span className="text-xs font-medium">Précision</span>
            </div>
            <p className="text-2xl font-bold text-card-foreground">{accuracy.toFixed(1)}%</p>
            <p className="text-xs text-muted-foreground">Cible: {'>'}98.5%</p>
          </div>

          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-success mb-1">
              <TrendingUp className="h-4 w-4" />
              <span className="text-xs font-medium">Rappel DoS</span>
            </div>
            <p className="text-2xl font-bold text-card-foreground">99.1%</p>
            <p className="text-xs text-muted-foreground">Cible: {'>'}99.0%</p>
          </div>

          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-warning mb-1">
              <Zap className="h-4 w-4" />
              <span className="text-xs font-medium">F1 Exploit</span>
            </div>
            <p className="text-2xl font-bold text-card-foreground">96.0%</p>
            <p className="text-xs text-muted-foreground">Cible: {'>'}95.0%</p>
          </div>

          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-center gap-1 text-destructive mb-1">
              <Target className="h-4 w-4" />
              <span className="text-xs font-medium">Faux Positifs</span>
            </div>
            <p className="text-2xl font-bold text-card-foreground">{falsePositiveRate.toFixed(2)}%</p>
            <p className="text-xs text-muted-foreground">Cible: {'<'}1.5%</p>
          </div>
        </div>
      </div>

      {/* Per-Class Metrics */}
      <div className="bg-card border border-border rounded-xl p-4">
        <h4 className="font-medium text-card-foreground mb-4">Métriques par Classe</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={classMetrics} layout="vertical" margin={{ left: 50 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.30 0.02 260)" horizontal={false} />
            <XAxis 
              type="number" 
              domain={[90, 100]} 
              tick={{ fill: 'oklch(0.65 0.01 260)', fontSize: 11 }}
              axisLine={{ stroke: 'oklch(0.30 0.02 260)' }}
            />
            <YAxis 
              type="category" 
              dataKey="name" 
              tick={{ fill: 'oklch(0.65 0.01 260)', fontSize: 11 }}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'oklch(0.18 0.02 260)',
                border: '1px solid oklch(0.30 0.02 260)',
                borderRadius: '8px',
                color: 'oklch(0.95 0.01 260)',
              }}
            />
            <Bar dataKey="precision" fill="oklch(0.65 0.20 175)" name="Précision" radius={[0, 4, 4, 0]} />
            <Bar dataKey="recall" fill="oklch(0.60 0.18 30)" name="Rappel" radius={[0, 4, 4, 0]} />
            <Bar dataKey="f1" fill="oklch(0.75 0.18 85)" name="F1-Score" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Ensemble Model Votes */}
      <div className="bg-card border border-border rounded-xl p-4">
        <h4 className="font-medium text-card-foreground mb-4">Modèle Ensemble (Stacking)</h4>
        <div className="space-y-3">
          {ensembleVotes.map((model) => (
            <div key={model.name} className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground w-28">{model.name}</span>
              <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all duration-500"
                  style={{ 
                    width: `${model.confidence}%`,
                    backgroundColor: model.color
                  }}
                />
              </div>
              <span className="text-sm font-medium text-card-foreground w-16 text-right">
                {model.confidence.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-4 text-center">
          Meta-classifieur: Régression Logistique avec vote pondéré
        </p>
      </div>

      {/* Autoencoder Status */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-card-foreground">Auto-encodeur (Zero-day)</h4>
          <span className="text-xs px-2 py-1 rounded-full bg-success/20 text-success">Actif</span>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Seuil d&apos;anomalie</span>
            <p className="font-medium text-card-foreground">95ème percentile</p>
          </div>
          <div>
            <span className="text-muted-foreground">Architecture</span>
            <p className="font-medium text-card-foreground">64-16-64 (DAE)</p>
          </div>
          <div>
            <span className="text-muted-foreground">Erreur moyenne</span>
            <p className="font-medium text-card-foreground">0.0023</p>
          </div>
          <div>
            <span className="text-muted-foreground">Anomalies détectées</span>
            <p className="font-medium text-destructive">3 aujourd&apos;hui</p>
          </div>
        </div>
      </div>
    </div>
  )
}
