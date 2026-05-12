'use client'

import { useState, useRef, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'
import { Bot, User, Send, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AIAgentMessage, Alert } from '@/lib/types'

interface AIAgentProps {
  messages: AIAgentMessage[]
  onSendMessage: (content: string) => void
  selectedAlert: Alert | null
}

export function AIAgent({ messages, onSendMessage, selectedAlert }: AIAgentProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    onSendMessage(input.trim())
    setInput('')
  }

  const quickActions = [
    { label: 'État du système', query: 'status' },
    { label: 'Résumé alertes', query: 'alertes récentes' },
    { label: 'Aide', query: 'aide' },
  ]

  return (
    <div className="bg-card border border-border rounded-xl flex flex-col h-[600px]">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Bot className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-card-foreground">Agent IA NIDS</h3>
            <p className="text-xs text-muted-foreground">Analyse et recommandations intelligentes</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-success pulse-glow" />
            <span className="text-xs text-success">En ligne</span>
          </div>
        </div>
      </div>

      {/* Selected Alert Context */}
      {selectedAlert && (
        <div className="p-3 bg-primary/5 border-b border-border">
          <div className="flex items-center gap-2 text-xs">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span className="text-primary font-medium">Contexte actif:</span>
            <span className="text-muted-foreground">
              {selectedAlert.attackType} depuis {selectedAlert.srcip}
            </span>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3",
              message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
            )}
          >
            <div className={cn(
              "p-2 rounded-lg shrink-0",
              message.role === 'user' ? 'bg-primary/10' : 'bg-muted'
            )}>
              {message.role === 'user' ? (
                <User className="h-4 w-4 text-primary" />
              ) : (
                <Bot className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
            
            <div className={cn(
              "flex-1 max-w-[80%]",
              message.role === 'user' ? 'text-right' : 'text-left'
            )}>
              <div className={cn(
                "inline-block p-3 rounded-xl text-sm",
                message.role === 'user' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted text-card-foreground'
              )}>
                <div 
                  className="prose prose-sm prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ 
                    __html: message.content
                      .replace(/\n/g, '<br />')
                      .replace(/#{1,3}\s(.+?)(<br \/>|$)/g, '<strong>$1</strong>$2')
                      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                      .replace(/- (.+?)(<br \/>|$)/g, '• $1<br />')
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {formatDistanceToNow(message.timestamp, { addSuffix: true, locale: fr })}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-t border-border">
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          <span className="text-xs text-muted-foreground shrink-0">Actions rapides:</span>
          {quickActions.map((action) => (
            <button
              key={action.label}
              onClick={() => onSendMessage(action.query)}
              className="px-3 py-1 text-xs font-medium rounded-full bg-muted text-muted-foreground hover:bg-primary/20 hover:text-primary transition-colors whitespace-nowrap"
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-border">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez une question sur la sécurité..."
            className="flex-1 px-4 py-2.5 bg-input border border-border rounded-lg text-sm text-card-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="p-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  )
}
