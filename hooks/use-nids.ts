'use client'

import { useState, useEffect, useCallback } from 'react'
import type { 
  Alert, 
  NetworkFlow, 
  SystemMetrics, 
  TrafficStats, 
  AIAgentMessage,
  DashboardState,
  SystemStatus
} from '@/lib/types'
import { 
  generateNetworkFlow, 
  generateAlertFromFlow, 
  generateSystemMetrics,
  generateTrafficHistory,
  getInitialAgentMessages,
  generateAIResponse,
  generateId
} from '@/lib/mock-data'

export function useNIDS() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('online')
  const [metrics, setMetrics] = useState<SystemMetrics>(generateSystemMetrics())
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [trafficHistory, setTrafficHistory] = useState<TrafficStats[]>([])
  const [recentFlows, setRecentFlows] = useState<NetworkFlow[]>([])
  const [agentMessages, setAgentMessages] = useState<AIAgentMessage[]>(getInitialAgentMessages())
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [isMonitoring, setIsMonitoring] = useState(true)

  // Initialiser l'historique du trafic
  useEffect(() => {
    setTrafficHistory(generateTrafficHistory(24))
  }, [])

  // Simuler le monitoring en temps réel
  useEffect(() => {
    if (!isMonitoring) return

    const interval = setInterval(() => {
      // Générer de nouveaux flux
      const newFlow = generateNetworkFlow()
      setRecentFlows(prev => [newFlow, ...prev.slice(0, 99)])

      // Vérifier si c'est une attaque et générer une alerte
      const alert = generateAlertFromFlow(newFlow)
      if (alert) {
        setAlerts(prev => [alert, ...prev.slice(0, 49)])
      }

      // Mettre à jour les métriques
      setMetrics(prev => ({
        ...prev,
        totalRequests: prev.totalRequests + 1,
        blockedRequests: alert ? prev.blockedRequests + 1 : prev.blockedRequests,
        allowedRequests: !alert ? prev.allowedRequests + 1 : prev.allowedRequests,
        avgLatency: 20 + Math.random() * 25,
        cpuUsage: 25 + Math.random() * 35,
        memoryUsage: 35 + Math.random() * 30,
        activeConnections: 200 + Math.floor(Math.random() * 300),
      }))

    }, 2000) // Nouvelle donnée toutes les 2 secondes

    return () => clearInterval(interval)
  }, [isMonitoring])

  // Mettre à jour l'historique du trafic toutes les minutes
  useEffect(() => {
    const interval = setInterval(() => {
      setTrafficHistory(prev => {
        const newStats: TrafficStats = {
          timestamp: new Date(),
          normal: Math.floor(800 + Math.random() * 200),
          dos: Math.floor(Math.random() * 30),
          exploit: Math.floor(Math.random() * 20),
          fuzzers: Math.floor(Math.random() * 15),
          reconnaissance: Math.floor(Math.random() * 25),
          other: Math.floor(Math.random() * 10),
          total: 0,
        }
        newStats.total = newStats.normal + newStats.dos + newStats.exploit + 
                         newStats.fuzzers + newStats.reconnaissance + newStats.other
        return [...prev.slice(1), newStats]
      })
    }, 60000)

    return () => clearInterval(interval)
  }, [])

  // Confirmer une alerte
  const confirmAlert = useCallback((alertId: string) => {
    setAlerts(prev => 
      prev.map(a => a.id === alertId ? { ...a, status: 'confirmed' } : a)
    )
  }, [])

  // Rejeter une alerte (faux positif)
  const dismissAlert = useCallback((alertId: string) => {
    setAlerts(prev => 
      prev.map(a => a.id === alertId ? { ...a, status: 'dismissed' } : a)
    )
  }, [])

  // Marquer une alerte en investigation
  const investigateAlert = useCallback((alertId: string) => {
    setAlerts(prev => 
      prev.map(a => a.id === alertId ? { ...a, status: 'investigating' } : a)
    )
  }, [])

  // Analyser une alerte avec l'agent IA
  const analyzeWithAI = useCallback((alert: Alert) => {
    setSelectedAlert(alert)
    
    // Ajouter la question de l'utilisateur
    const userMessage: AIAgentMessage = {
      id: generateId(),
      role: 'user',
      content: `Analyse l'alerte ${alert.attackType} provenant de ${alert.srcip}`,
      timestamp: new Date(),
      alertContext: alert,
    }
    
    // Générer la réponse de l'IA
    const aiResponse: AIAgentMessage = {
      id: generateId(),
      role: 'assistant',
      content: generateAIResponse(alert),
      timestamp: new Date(),
      alertContext: alert,
    }
    
    setAgentMessages(prev => [...prev, userMessage, aiResponse])
  }, [])

  // Envoyer un message à l'agent IA
  const sendAgentMessage = useCallback((content: string) => {
    const userMessage: AIAgentMessage = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
    }
    
    setAgentMessages(prev => [...prev, userMessage])
    
    // Simuler une réponse de l'IA
    setTimeout(() => {
      let response = ''
      
      if (content.toLowerCase().includes('status') || content.toLowerCase().includes('état')) {
        response = `## État du Système\n\n- **Statut:** ${systemStatus === 'online' ? '🟢 En ligne' : '🔴 Hors ligne'}\n- **Requêtes totales:** ${metrics.totalRequests.toLocaleString()}\n- **Menaces bloquées:** ${metrics.blockedRequests}\n- **Latence moyenne:** ${metrics.avgLatency.toFixed(1)}ms\n- **Précision du modèle:** ${metrics.modelAccuracy.toFixed(1)}%`
      } else if (content.toLowerCase().includes('help') || content.toLowerCase().includes('aide')) {
        response = `## Commandes Disponibles\n\n- **"status"** - Afficher l'état du système\n- **"alertes"** - Voir les alertes récentes\n- **"rapport"** - Générer un rapport de sécurité\n- Sélectionnez une alerte pour une analyse détaillée`
      } else if (content.toLowerCase().includes('alerte')) {
        const pendingAlerts = alerts.filter(a => a.status === 'pending').length
        response = `## Résumé des Alertes\n\n- **En attente:** ${pendingAlerts}\n- **Total:** ${alerts.length}\n\nLes attaques les plus fréquentes sont:\n- DoS (${alerts.filter(a => a.attackType === 'DoS').length})\n- Reconnaissance (${alerts.filter(a => a.attackType === 'Reconnaissance').length})\n- Exploit (${alerts.filter(a => a.attackType === 'Exploit').length})`
      } else {
        response = `J'ai bien reçu votre message. Pour une analyse détaillée, veuillez sélectionner une alerte spécifique dans le panneau de gauche, ou utilisez les commandes suivantes:\n\n- **status** - État du système\n- **alertes** - Résumé des alertes\n- **aide** - Liste des commandes`
      }
      
      const aiMessage: AIAgentMessage = {
        id: generateId(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      }
      
      setAgentMessages(prev => [...prev, aiMessage])
    }, 1000)
  }, [systemStatus, metrics, alerts])

  // Toggle monitoring
  const toggleMonitoring = useCallback(() => {
    setIsMonitoring(prev => !prev)
    setSystemStatus(prev => prev === 'online' ? 'degraded' : 'online')
  }, [])

  // Calculer le niveau de menace actif
  const getActiveThreatLevel = useCallback(() => {
    const criticalAlerts = alerts.filter(a => a.threatLevel === 'critical' && a.status === 'pending').length
    const highAlerts = alerts.filter(a => a.threatLevel === 'high' && a.status === 'pending').length
    
    if (criticalAlerts > 0) return 'critical'
    if (highAlerts > 2) return 'critical'
    if (highAlerts > 0) return 'high'
    if (alerts.filter(a => a.status === 'pending').length > 5) return 'medium'
    return 'low'
  }, [alerts])

  return {
    // État
    systemStatus,
    metrics,
    alerts,
    trafficHistory,
    recentFlows,
    agentMessages,
    selectedAlert,
    isMonitoring,
    activeThreatLevel: getActiveThreatLevel(),
    
    // Actions
    confirmAlert,
    dismissAlert,
    investigateAlert,
    analyzeWithAI,
    sendAgentMessage,
    toggleMonitoring,
    setSelectedAlert,
  }
}
