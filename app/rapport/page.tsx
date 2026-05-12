'use client'

import { useState } from 'react'
import { 
  FileText, 
  Download, 
  BookOpen, 
  Brain, 
  Shield, 
  BarChart3,
  Database,
  Code2,
  Lock,
  ArrowLeft,
  CheckCircle2,
  Loader2
} from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { downloadProjectReport } from '@/lib/generate-report-pdf'

const sections = [
  {
    num: '1',
    title: 'Introduction et Contexte',
    icon: BookOpen,
    description: 'Problématique, objectifs et périmètre fonctionnel du projet NIDS',
    topics: ['Menaces cybernétiques actuelles', 'Limites des IDS traditionnels', 'Objectifs de performance']
  },
  {
    num: '2',
    title: 'Architecture du Système',
    icon: Code2,
    description: 'Architecture modulaire en trois couches (Frontend, Backend, Agent IA)',
    topics: ['Module A - Interface Métier', 'Module B - Security Engine', 'Module C - Agent IA']
  },
  {
    num: '3',
    title: 'Algorithmes de Machine Learning',
    icon: Brain,
    description: 'Modèle ensemble hybride et auto-encodeur pour détection zero-day',
    topics: ['LightGBM - Rapidité et patterns', 'XGBoost - Précision et régularisation', 'Random Forest - Stabilité', 'Auto-encodeur - Zero-day', 'SHAP - Explicabilité']
  },
  {
    num: '4',
    title: 'Dataset UNSW-NB15',
    icon: Database,
    description: 'Benchmark moderne avec 2.5M enregistrements et 9 catégories d\'attaques',
    topics: ['42 features sélectionnées', 'Distribution des classes', 'Gestion du déséquilibre']
  },
  {
    num: '5',
    title: 'Métriques de Performance',
    icon: BarChart3,
    description: 'Résultats du modèle ensemble et de l\'auto-encodeur',
    topics: ['Accuracy: 96.8%', 'F1-Score: 96.3%', 'Faux positifs: 1.8%', 'Latence: 45ms']
  },
  {
    num: '6',
    title: 'Interface Utilisateur',
    icon: FileText,
    description: 'Technologies frontend et composants de l\'application',
    topics: ['Next.js 15 + React 19', '14 composants spécialisés', 'Design system cohérent']
  },
  {
    num: '7',
    title: 'API et Intégrations',
    icon: Code2,
    description: 'Endpoints REST et intégrations SIEM/SOAR',
    topics: ['8 endpoints API', 'Format JSON standardisé', 'Intégrations Splunk, Elastic, QRadar']
  },
  {
    num: '8',
    title: 'Sécurité et Conformité',
    icon: Lock,
    description: 'Mesures de sécurité et conformité réglementaire',
    topics: ['JWT + MFA', 'RBAC', 'RGPD, ISO 27001', 'Chiffrement AES-256']
  },
]

export default function RapportPage() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [isGenerated, setIsGenerated] = useState(false)

  const handleDownload = async () => {
    setIsGenerating(true)
    
    // Simulate a small delay for better UX
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    try {
      downloadProjectReport()
      setIsGenerated(true)
      setTimeout(() => setIsGenerated(false), 3000)
    } catch (error) {
      console.error('Erreur lors de la génération:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm" className="gap-2">
                  <ArrowLeft className="h-4 w-4" />
                  Retour au Dashboard
                </Button>
              </Link>
              <div className="h-6 w-px bg-border" />
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-foreground">Rapport Technique</h1>
                  <p className="text-sm text-muted-foreground">Documentation complète du projet NIDS Cyber-IA</p>
                </div>
              </div>
            </div>
            
            <Button 
              onClick={handleDownload} 
              disabled={isGenerating}
              className="gap-2"
              size="lg"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Génération en cours...
                </>
              ) : isGenerated ? (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  Téléchargé !
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" />
                  Télécharger le PDF
                </>
              )}
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Hero Section */}
        <div className="mb-12 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-primary/60 mb-6">
            <Shield className="h-10 w-10 text-primary-foreground" />
          </div>
          <h2 className="text-3xl font-bold text-foreground mb-4">
            NIDS Cyber-IA - Rapport Technique Complet
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Ce rapport détaille l&apos;architecture, les algorithmes de machine learning, 
            les métriques de performance et les choix techniques du système de détection d&apos;intrusion intelligent.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {[
            { label: 'Pages', value: '17+', icon: FileText },
            { label: 'Sections', value: '9', icon: BookOpen },
            { label: 'Tableaux', value: '15+', icon: BarChart3 },
            { label: 'Diagrammes', value: '5', icon: Code2 },
          ].map((stat) => (
            <Card key={stat.label} className="bg-card/50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <stat.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Sections Overview */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold text-foreground mb-6">Contenu du Rapport</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {sections.map((section) => (
              <Card key={section.num} className="bg-card/50 hover:bg-card/80 transition-colors">
                <CardHeader className="pb-3">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <section.icon className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">
                        <span className="text-primary mr-2">{section.num}.</span>
                        {section.title}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {section.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex flex-wrap gap-2">
                    {section.topics.map((topic) => (
                      <span 
                        key={topic}
                        className="px-2 py-1 text-xs rounded-md bg-muted text-muted-foreground"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Algorithm Details */}
        <Card className="mb-8 bg-card/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              Pourquoi ces Algorithmes ?
            </CardTitle>
            <CardDescription>
              Justification des choix techniques pour le modèle ensemble hybride
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <span className="text-sm font-bold text-blue-500">40%</span>
                  </div>
                  <h4 className="font-semibold text-foreground">LightGBM</h4>
                </div>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>100x plus rapide que XGBoost classique</li>
                  <li>Gestion efficace des features catégorielles</li>
                  <li>Faible consommation mémoire</li>
                  <li>Excellent pour les données déséquilibrées</li>
                </ul>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                    <span className="text-sm font-bold text-green-500">35%</span>
                  </div>
                  <h4 className="font-semibold text-foreground">XGBoost</h4>
                </div>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>Régularisation L1/L2 intégrée</li>
                  <li>Gestion native des valeurs manquantes</li>
                  <li>Performance de pointe en compétitions</li>
                  <li>Pruning intelligent des arbres</li>
                </ul>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <span className="text-sm font-bold text-purple-500">25%</span>
                  </div>
                  <h4 className="font-semibold text-foreground">Random Forest</h4>
                </div>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>Résistance au bruit et outliers</li>
                  <li>Estimation de l&apos;importance des features</li>
                  <li>Parallélisation native</li>
                  <li>Faible variance par agrégation</li>
                </ul>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-amber-500/10 rounded-lg border border-amber-500/20">
              <div className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                  <Brain className="h-4 w-4 text-amber-500" />
                </div>
                <div>
                  <h4 className="font-semibold text-foreground mb-1">Auto-encodeur pour Zero-Day</h4>
                  <p className="text-sm text-muted-foreground">
                    L&apos;auto-encodeur apprend la distribution du trafic normal et détecte les anomalies 
                    via l&apos;erreur de reconstruction. Les attaques zero-day, jamais vues à l&apos;entraînement, 
                    produisent une erreur élevée (score {'>'}1) permettant leur détection sans signature préalable.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* CTA */}
        <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
          <CardContent className="py-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div>
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  Prêt à télécharger le rapport complet ?
                </h3>
                <p className="text-muted-foreground">
                  Le PDF contient 17+ pages de documentation technique détaillée, 
                  incluant tous les diagrammes, tableaux et références.
                </p>
              </div>
              <Button 
                onClick={handleDownload} 
                disabled={isGenerating}
                size="lg"
                className="gap-2 min-w-[200px]"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Génération...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Télécharger le PDF
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
