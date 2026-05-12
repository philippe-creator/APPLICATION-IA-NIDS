'use client'

import { cn } from '@/lib/utils'
import type { ShapExplanation } from '@/lib/types'

interface ShapVisualizationProps {
  explanations: ShapExplanation[]
  title?: string
}

export function ShapVisualization({ explanations, title = 'Explicabilité SHAP' }: ShapVisualizationProps) {
  const maxShap = Math.max(...explanations.map(e => Math.abs(e.shapValue)))
  
  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="mb-4">
        <h3 className="font-semibold text-card-foreground">{title}</h3>
        <p className="text-xs text-muted-foreground">
          Contribution de chaque variable à la décision du modèle
        </p>
      </div>
      
      <div className="space-y-3">
        {explanations.map((explanation, index) => {
          const percentage = (Math.abs(explanation.shapValue) / maxShap) * 100
          const isPositive = explanation.contribution === 'positive'
          
          return (
            <div key={index} className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-primary">{explanation.feature}</span>
                  <span className="text-muted-foreground">=</span>
                  <span className="text-card-foreground">{explanation.value.toFixed(2)}</span>
                </div>
                <span className={cn(
                  "text-xs font-medium",
                  isPositive ? "text-destructive" : "text-success"
                )}>
                  {isPositive ? '+' : ''}{explanation.shapValue.toFixed(3)}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      isPositive ? "bg-destructive" : "bg-success"
                    )}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <span className={cn(
                  "text-xs shrink-0",
                  isPositive ? "text-destructive" : "text-success"
                )}>
                  {isPositive ? '↑ Risque' : '↓ Risque'}
                </span>
              </div>
              
              <p className="text-xs text-muted-foreground">
                {explanation.description}
              </p>
            </div>
          )
        })}
      </div>
      
      {/* Légende */}
      <div className="mt-4 pt-4 border-t border-border">
        <div className="flex items-center justify-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-destructive" />
            <span className="text-muted-foreground">Augmente le risque</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-success" />
            <span className="text-muted-foreground">Diminue le risque</span>
          </div>
        </div>
      </div>
    </div>
  )
}
