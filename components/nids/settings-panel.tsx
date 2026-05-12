'use client'

import { useState } from 'react'
import { 
  Settings, 
  Bell, 
  Shield, 
  Database, 
  Cpu, 
  RefreshCw,
  Save,
  ToggleLeft,
  ToggleRight,
  Info
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface SettingsState {
  realTimeMonitoring: boolean
  autoBlock: boolean
  emailNotifications: boolean
  slackNotifications: boolean
  criticalAlertsOnly: boolean
  sensitivityLevel: 'low' | 'medium' | 'high'
  modelUpdateFrequency: 'daily' | 'weekly' | 'monthly'
  dataRetention: number
  maxLatency: number
}

export function SettingsPanel() {
  const [settings, setSettings] = useState<SettingsState>({
    realTimeMonitoring: true,
    autoBlock: true,
    emailNotifications: true,
    slackNotifications: false,
    criticalAlertsOnly: false,
    sensitivityLevel: 'medium',
    modelUpdateFrequency: 'weekly',
    dataRetention: 30,
    maxLatency: 50,
  })
  
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const toggleSetting = (key: keyof SettingsState) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Settings className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-card-foreground">Configuration du NIDS</h3>
            <p className="text-xs text-muted-foreground">Paramètres du système de détection</p>
          </div>
        </div>
      </div>

      {/* Monitoring Settings */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="h-4 w-4 text-primary" />
          <h4 className="font-medium text-card-foreground">Surveillance</h4>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-card-foreground">Monitoring temps réel</p>
              <p className="text-xs text-muted-foreground">Analyser le trafic en continu</p>
            </div>
            <button 
              onClick={() => toggleSetting('realTimeMonitoring')}
              className="text-primary"
            >
              {settings.realTimeMonitoring ? (
                <ToggleRight className="h-8 w-8" />
              ) : (
                <ToggleLeft className="h-8 w-8 text-muted-foreground" />
              )}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-card-foreground">Blocage automatique</p>
              <p className="text-xs text-muted-foreground">Bloquer les menaces critiques automatiquement</p>
            </div>
            <button 
              onClick={() => toggleSetting('autoBlock')}
              className="text-primary"
            >
              {settings.autoBlock ? (
                <ToggleRight className="h-8 w-8" />
              ) : (
                <ToggleLeft className="h-8 w-8 text-muted-foreground" />
              )}
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-card-foreground">Niveau de sensibilité</p>
              <span className="text-xs text-primary font-medium capitalize">{settings.sensitivityLevel}</span>
            </div>
            <div className="flex gap-1">
              {(['low', 'medium', 'high'] as const).map((level) => (
                <button
                  key={level}
                  onClick={() => setSettings(prev => ({ ...prev, sensitivityLevel: level }))}
                  className={cn(
                    "flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors",
                    settings.sensitivityLevel === level
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  )}
                >
                  {level === 'low' ? 'Faible' : level === 'medium' ? 'Moyen' : 'Élevé'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="h-4 w-4 text-primary" />
          <h4 className="font-medium text-card-foreground">Notifications</h4>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-card-foreground">Notifications email</p>
              <p className="text-xs text-muted-foreground">Recevoir les alertes par email</p>
            </div>
            <button 
              onClick={() => toggleSetting('emailNotifications')}
              className="text-primary"
            >
              {settings.emailNotifications ? (
                <ToggleRight className="h-8 w-8" />
              ) : (
                <ToggleLeft className="h-8 w-8 text-muted-foreground" />
              )}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-card-foreground">Intégration Slack</p>
              <p className="text-xs text-muted-foreground">Envoyer les alertes vers Slack</p>
            </div>
            <button 
              onClick={() => toggleSetting('slackNotifications')}
              className="text-primary"
            >
              {settings.slackNotifications ? (
                <ToggleRight className="h-8 w-8" />
              ) : (
                <ToggleLeft className="h-8 w-8 text-muted-foreground" />
              )}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-card-foreground">Alertes critiques uniquement</p>
              <p className="text-xs text-muted-foreground">Filtrer les notifications</p>
            </div>
            <button 
              onClick={() => toggleSetting('criticalAlertsOnly')}
              className="text-primary"
            >
              {settings.criticalAlertsOnly ? (
                <ToggleRight className="h-8 w-8" />
              ) : (
                <ToggleLeft className="h-8 w-8 text-muted-foreground" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Model Settings */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="h-4 w-4 text-primary" />
          <h4 className="font-medium text-card-foreground">Modèle ML</h4>
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-card-foreground">Fréquence de mise à jour</p>
            </div>
            <div className="flex gap-1">
              {(['daily', 'weekly', 'monthly'] as const).map((freq) => (
                <button
                  key={freq}
                  onClick={() => setSettings(prev => ({ ...prev, modelUpdateFrequency: freq }))}
                  className={cn(
                    "flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors",
                    settings.modelUpdateFrequency === freq
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  )}
                >
                  {freq === 'daily' ? 'Quotidien' : freq === 'weekly' ? 'Hebdo' : 'Mensuel'}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-card-foreground">Latence max (ms)</p>
              <span className="text-xs text-primary font-medium">{settings.maxLatency}ms</span>
            </div>
            <input
              type="range"
              min="20"
              max="120"
              value={settings.maxLatency}
              onChange={(e) => setSettings(prev => ({ ...prev, maxLatency: parseInt(e.target.value) }))}
              className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>20ms</span>
              <span>120ms</span>
            </div>
          </div>
        </div>
      </div>

      {/* Data Retention */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <Database className="h-4 w-4 text-primary" />
          <h4 className="font-medium text-card-foreground">Données</h4>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-card-foreground">Rétention des données (jours)</p>
            <span className="text-xs text-primary font-medium">{settings.dataRetention} jours</span>
          </div>
          <input
            type="range"
            min="7"
            max="90"
            value={settings.dataRetention}
            onChange={(e) => setSettings(prev => ({ ...prev, dataRetention: parseInt(e.target.value) }))}
            className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>7 jours</span>
            <span>90 jours</span>
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="bg-primary/5 border border-primary/20 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-card-foreground font-medium">Architecture Sidecar</p>
            <p className="text-xs text-muted-foreground mt-1">
              Le système utilise le pattern Sidecar pour isoler le moteur ML du module métier. 
              Communication via localhost pour une latence minimale. Modèle ensemble (LightGBM + XGBoost + RF) 
              avec auto-encodeur pour les attaques Zero-day.
            </p>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        className={cn(
          "w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all",
          saved 
            ? "bg-success text-success-foreground" 
            : "bg-primary text-primary-foreground hover:bg-primary/90"
        )}
      >
        {saved ? (
          <>
            <RefreshCw className="h-4 w-4" />
            Paramètres sauvegardés !
          </>
        ) : (
          <>
            <Save className="h-4 w-4" />
            Sauvegarder les paramètres
          </>
        )}
      </button>
    </div>
  )
}
