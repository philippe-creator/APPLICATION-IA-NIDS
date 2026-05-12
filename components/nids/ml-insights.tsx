'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Brain, 
  BarChart3, 
  Layers, 
  Target, 
  Cpu, 
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Sparkles,
} from 'lucide-react'
import { generateModelMetrics, type ModelMetrics } from '@/lib/ml-engine'
import type { AttackCategory } from '@/lib/types'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  Cell,
} from 'recharts'

export function MLInsights() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null)
  const [activeTab, setActiveTab] = useState('performance')
  
  useEffect(() => {
    setMetrics(generateModelMetrics())
    const interval = setInterval(() => {
      setMetrics(generateModelMetrics())
    }, 10000)
    return () => clearInterval(interval)
  }, [])
  
  if (!metrics) return null
  
  // Données pour le graphique radar
  const radarData = [
    { metric: 'Précision', value: metrics.precision },
    { metric: 'Rappel', value: metrics.recall },
    { metric: 'F1-Score', value: metrics.f1Score },
    { metric: 'AUC-ROC', value: metrics.aucRoc * 100 },
    { metric: 'TPR', value: metrics.truePositiveRate },
  ]
  
  // Données par classe pour le bar chart
  const classData = Object.entries(metrics.perClassMetrics)
    .filter(([cat]) => cat !== 'Normal')
    .map(([category, m]) => ({
      category: category.slice(0, 6),
      fullName: category,
      precision: m.precision,
      recall: m.recall,
      f1: m.f1Score,
      support: m.support,
    }))
    .slice(0, 8)
  
  // Couleurs pour les catégories
  const categoryColors: Record<string, string> = {
    DoS: '#ef4444',
    Exploit: '#f97316',
    Fuzzers: '#eab308',
    Reconnaissance: '#22c55e',
    Worms: '#8b5cf6',
    Backdoors: '#ec4899',
    Shellcode: '#06b6d4',
    Generic: '#6366f1',
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/20">
            <Brain className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-card-foreground">Intelligence ML</h2>
            <p className="text-sm text-muted-foreground">
              Modèle Hybrid Ensemble (LightGBM + XGBoost + RandomForest)
            </p>
          </div>
        </div>
        <Badge className="bg-success/20 text-success border-success/30">
          <Sparkles className="h-3 w-3 mr-1" />
          v2.1.0 - Actif
        </Badge>
      </div>
      
      {/* Métriques globales */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">Accuracy</span>
              <Target className="h-4 w-4 text-primary" />
            </div>
            <p className="text-2xl font-bold text-primary">{metrics.accuracy.toFixed(2)}%</p>
            <Progress value={metrics.accuracy} className="h-1 mt-2" />
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">F1-Score</span>
              <BarChart3 className="h-4 w-4 text-chart-5" />
            </div>
            <p className="text-2xl font-bold text-chart-5">{metrics.f1Score.toFixed(2)}%</p>
            <Progress value={metrics.f1Score} className="h-1 mt-2" />
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">Faux Positifs</span>
              <AlertCircle className="h-4 w-4 text-warning" />
            </div>
            <p className="text-2xl font-bold text-warning">{metrics.falsePositiveRate.toFixed(2)}%</p>
            <Progress value={metrics.falsePositiveRate * 10} className="h-1 mt-2" />
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">Latence</span>
              <Cpu className="h-4 w-4 text-chart-3" />
            </div>
            <p className="text-2xl font-bold text-chart-3">{metrics.inferenceLatency.toFixed(1)}ms</p>
            <Progress value={100 - metrics.inferenceLatency} className="h-1 mt-2" />
          </CardContent>
        </Card>
      </div>
      
      {/* Onglets détaillés */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-muted">
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="perclass">Par Classe</TabsTrigger>
          <TabsTrigger value="ensemble">Ensemble</TabsTrigger>
          <TabsTrigger value="autoencoder">Auto-encodeur</TabsTrigger>
        </TabsList>
        
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Radar Chart */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Métriques Globales</CardTitle>
                <CardDescription>Performance du modèle ensemble</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="var(--border)" />
                      <PolarAngleAxis 
                        dataKey="metric" 
                        tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                      />
                      <PolarRadiusAxis 
                        angle={30} 
                        domain={[0, 100]} 
                        tick={{ fontSize: 10 }}
                      />
                      <Radar
                        name="Performance"
                        dataKey="value"
                        stroke="var(--primary)"
                        fill="var(--primary)"
                        fillOpacity={0.3}
                        strokeWidth={2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
            
            {/* Détails */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Objectifs de Performance</CardTitle>
                <CardDescription>Basé sur le cahier des charges UNSW-NB15</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { label: 'Précision Globale', target: 98.5, current: metrics.accuracy, icon: Target },
                  { label: 'Rappel (DoS)', target: 99.0, current: metrics.perClassMetrics.DoS.recall, icon: TrendingUp },
                  { label: 'F1-Score (Exploit)', target: 95.0, current: metrics.perClassMetrics.Exploit.f1Score, icon: BarChart3 },
                  { label: 'Latence Inférence', target: 120, current: metrics.inferenceLatency, icon: Cpu, unit: 'ms', reverse: true },
                ].map((item, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <item.icon className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{item.label}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          {item.current.toFixed(1)}{item.unit || '%'}
                        </span>
                        {item.reverse 
                          ? item.current <= item.target 
                            ? <CheckCircle2 className="h-4 w-4 text-success" />
                            : <AlertCircle className="h-4 w-4 text-warning" />
                          : item.current >= item.target
                            ? <CheckCircle2 className="h-4 w-4 text-success" />
                            : <AlertCircle className="h-4 w-4 text-warning" />
                        }
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress 
                        value={item.reverse 
                          ? Math.min(100, (item.target / item.current) * 100)
                          : (item.current / item.target) * 100
                        } 
                        className="h-2 flex-1" 
                      />
                      <span className="text-xs text-muted-foreground w-16">
                        Cible: {item.target}{item.unit || '%'}
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="perclass" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Performance par Type d&apos;Attaque</CardTitle>
              <CardDescription>Précision, Rappel et F1-Score par catégorie</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={classData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis 
                      dataKey="category" 
                      tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                    />
                    <YAxis 
                      domain={[80, 100]} 
                      tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'var(--card)', 
                        border: '1px solid var(--border)',
                        borderRadius: '8px',
                      }}
                      formatter={(value: number, name: string) => [
                        `${value.toFixed(1)}%`,
                        name === 'precision' ? 'Précision' : name === 'recall' ? 'Rappel' : 'F1-Score'
                      ]}
                      labelFormatter={(label) => {
                        const item = classData.find(d => d.category === label)
                        return item?.fullName || label
                      }}
                    />
                    <Legend 
                      formatter={(value) => 
                        value === 'precision' ? 'Précision' : 
                        value === 'recall' ? 'Rappel' : 'F1-Score'
                      }
                    />
                    <Bar dataKey="precision" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="recall" fill="var(--chart-5)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="f1" fill="var(--chart-3)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          
          {/* Tableau détaillé */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Détail par Catégorie</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Catégorie</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Précision</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Rappel</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">F1</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Support</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(metrics.perClassMetrics)
                      .filter(([cat]) => cat !== 'Normal')
                      .map(([category, m]) => (
                        <tr key={category} className="border-b border-border/50 hover:bg-muted/30">
                          <td className="py-2 px-3">
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-2 h-2 rounded-full" 
                                style={{ backgroundColor: categoryColors[category] || 'var(--muted-foreground)' }}
                              />
                              {category}
                            </div>
                          </td>
                          <td className="text-right py-2 px-3">{m.precision.toFixed(1)}%</td>
                          <td className="text-right py-2 px-3">{m.recall.toFixed(1)}%</td>
                          <td className="text-right py-2 px-3 font-medium">{m.f1Score.toFixed(1)}%</td>
                          <td className="text-right py-2 px-3 text-muted-foreground">
                            {m.support.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="ensemble" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { name: 'LightGBM', weight: 40, desc: 'Vitesse et faible mémoire', color: 'primary' },
              { name: 'XGBoost', weight: 35, desc: 'Précision de pointe', color: 'chart-5' },
              { name: 'RandomForest', weight: 25, desc: 'Diversité structurelle', color: 'chart-3' },
            ].map((model) => (
              <Card key={model.name} className="bg-card border-border">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Layers className="h-4 w-4" />
                      {model.name}
                    </CardTitle>
                    <Badge variant="outline">{model.weight}%</Badge>
                  </div>
                  <CardDescription>{model.desc}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Poids dans l&apos;ensemble</span>
                      <span className="font-medium">{model.weight}%</span>
                    </div>
                    <Progress value={model.weight} className="h-2" />
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 rounded bg-muted/30 text-center">
                        <p className="text-muted-foreground">Contribution</p>
                        <p className="font-medium">{(model.weight / 100 * metrics.accuracy).toFixed(1)}%</p>
                      </div>
                      <div className="p-2 rounded bg-muted/30 text-center">
                        <p className="text-muted-foreground">Votes</p>
                        <p className="font-medium">~{Math.floor(1000 * model.weight / 100)}/1000</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Architecture Stacking</CardTitle>
              <CardDescription>
                Le méta-classifieur agrège les prédictions des modèles de base
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center gap-4 p-4">
                <div className="flex flex-col items-center gap-2">
                  <div className="p-3 rounded-lg bg-primary/20 border border-primary/30">
                    <span className="text-sm font-medium">LightGBM</span>
                  </div>
                  <div className="p-3 rounded-lg bg-chart-5/20 border border-chart-5/30">
                    <span className="text-sm font-medium">XGBoost</span>
                  </div>
                  <div className="p-3 rounded-lg bg-chart-3/20 border border-chart-3/30">
                    <span className="text-sm font-medium">RandomForest</span>
                  </div>
                </div>
                <div className="flex items-center">
                  <div className="w-16 h-0.5 bg-border" />
                  <div className="text-muted-foreground">→</div>
                </div>
                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <p className="text-sm font-medium text-center">Voting Classifier</p>
                  <p className="text-xs text-muted-foreground text-center mt-1">Pondéré</p>
                </div>
                <div className="flex items-center">
                  <div className="text-muted-foreground">→</div>
                  <div className="w-16 h-0.5 bg-border" />
                </div>
                <div className="p-4 rounded-lg bg-success/20 border border-success/30">
                  <p className="text-sm font-medium text-center">Prédiction</p>
                  <p className="text-xs text-success text-center mt-1">Finale</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="autoencoder" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-chart-4" />
                Denoising Autoencoder
              </CardTitle>
              <CardDescription>
                Détection d&apos;attaques Zero-day par analyse d&apos;anomalies
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Architecture */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Architecture du réseau</h4>
                  <div className="flex items-center justify-center gap-2 p-4 bg-muted/30 rounded-lg">
                    <div className="text-center">
                      <div className="w-16 h-20 bg-primary/20 rounded flex items-center justify-center border border-primary/30">
                        <span className="text-xs">Input<br/>64</span>
                      </div>
                    </div>
                    <span className="text-muted-foreground">→</span>
                    <div className="text-center">
                      <div className="w-12 h-16 bg-primary/30 rounded flex items-center justify-center border border-primary/40">
                        <span className="text-xs">32</span>
                      </div>
                    </div>
                    <span className="text-muted-foreground">→</span>
                    <div className="text-center">
                      <div className="w-8 h-12 bg-chart-4/40 rounded flex items-center justify-center border border-chart-4/50">
                        <span className="text-xs">16</span>
                      </div>
                      <span className="text-xs text-muted-foreground mt-1 block">Latent</span>
                    </div>
                    <span className="text-muted-foreground">→</span>
                    <div className="text-center">
                      <div className="w-12 h-16 bg-primary/30 rounded flex items-center justify-center border border-primary/40">
                        <span className="text-xs">32</span>
                      </div>
                    </div>
                    <span className="text-muted-foreground">→</span>
                    <div className="text-center">
                      <div className="w-16 h-20 bg-success/20 rounded flex items-center justify-center border border-success/30">
                        <span className="text-xs">Output<br/>64</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Paramètres */}
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Paramètres</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between p-2 rounded bg-muted/30">
                      <span className="text-sm text-muted-foreground">Couches cachées</span>
                      <span className="text-sm font-medium">64 → 32 → 16 → 32 → 64</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-muted/30">
                      <span className="text-sm text-muted-foreground">Bruit gaussien</span>
                      <span className="text-sm font-medium">σ = 0.1</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-muted/30">
                      <span className="text-sm text-muted-foreground">Seuil d&apos;anomalie</span>
                      <span className="text-sm font-medium">95ème percentile</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-muted/30">
                      <span className="text-sm text-muted-foreground">Fonction perte</span>
                      <span className="text-sm font-medium">MSE (Reconstruction)</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Fonctionnement */}
              <div className="p-4 rounded-lg border border-border bg-muted/20">
                <h4 className="text-sm font-medium mb-2">Principe de détection Zero-day</h4>
                <p className="text-sm text-muted-foreground">
                  L&apos;auto-encodeur est entraîné exclusivement sur du trafic normal. Lors de l&apos;inférence, 
                  si l&apos;erreur de reconstruction dépasse le seuil (95ème percentile), le flux est 
                  considéré comme une anomalie potentielle - possiblement une attaque Zero-day non 
                  vue lors de l&apos;entraînement.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
