'use client'

import { ArrowLeft, ExternalLink, Bot } from 'lucide-react'
import Link from 'next/link'

export default function ChatPage() {
  return (
    <div className="min-h-screen gradient-bg">
      {/* Header */}
      <div className="bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link 
                href="/" 
                className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Back to Home
              </Link>
              <div className="h-6 w-px bg-border" />
              <div className="flex items-center space-x-2">
                <Bot className="w-5 h-5 text-primary" />
                <h1 className="text-xl font-semibold text-foreground">Investment Chatbot</h1>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <ExternalLink className="w-4 h-4" />
              <span>Powered by OpenAI</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chat iframe */}
      <iframe 
        src="https://investment-chatbot-1.vercel.app/" 
        className="w-full h-[calc(100vh-4rem)] border-0"
        title="Investment Chatbot"
      />
    </div>
  )
}
