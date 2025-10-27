import Link from 'next/link'
import { Calculator, MessageCircle, TrendingUp, Shield, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function Home() {
  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-5">
      <div className="max-w-4xl w-full text-center">
        {/* Header */}
        <div className="mb-12 animate-fade-in">
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-4 gradient-text">
            Fargason Capital
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
            Professional investment portfolio tools and advisory services powered by advanced analytics
          </p>
        </div>

        {/* Main Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12 animate-slide-up">
          <Link href="/calculator" className="group">
            <div className="bg-card/80 backdrop-blur-sm border border-border rounded-xl p-8 h-full card-hover">
              <div className="flex items-center justify-center w-16 h-16 bg-primary/10 rounded-xl mb-6 mx-auto group-hover:bg-primary/20 transition-colors">
                <Calculator className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-3">
                Portfolio Calculator
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                Analyze portfolio returns, volatility, and performance over time with custom asset allocations and rebalancing strategies
              </p>
              <div className="mt-4 flex items-center justify-center text-sm text-primary font-medium">
                <TrendingUp className="w-4 h-4 mr-2" />
                Advanced Analytics
              </div>
            </div>
          </Link>

          <Link href="/chat" className="group">
            <div className="bg-card/80 backdrop-blur-sm border border-border rounded-xl p-8 h-full card-hover">
              <div className="flex items-center justify-center w-16 h-16 bg-primary/10 rounded-xl mb-6 mx-auto group-hover:bg-primary/20 transition-colors">
                <MessageCircle className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-3">
                Investment Chatbot
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                Ask questions about investments, portfolio strategies, and financial planning with AI-powered insights
              </p>
              <div className="mt-4 flex items-center justify-center text-sm text-primary font-medium">
                <Zap className="w-4 h-4 mr-2" />
                AI-Powered
              </div>
            </div>
          </Link>
        </div>

        {/* Features Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-slide-up">
          <div className="bg-card/40 backdrop-blur-sm border border-border rounded-lg p-4">
            <Shield className="w-6 h-6 text-primary mb-2 mx-auto" />
            <h3 className="font-semibold text-sm mb-1">Secure & Private</h3>
            <p className="text-xs text-muted-foreground">Your data is protected with enterprise-grade security</p>
          </div>
          <div className="bg-card/40 backdrop-blur-sm border border-border rounded-lg p-4">
            <TrendingUp className="w-6 h-6 text-primary mb-2 mx-auto" />
            <h3 className="font-semibold text-sm mb-1">Real-Time Data</h3>
            <p className="text-xs text-muted-foreground">Live market data from Yahoo Finance and other sources</p>
          </div>
          <div className="bg-card/40 backdrop-blur-sm border border-border rounded-lg p-4">
            <Calculator className="w-6 h-6 text-primary mb-2 mx-auto" />
            <h3 className="font-semibold text-sm mb-1">Professional Tools</h3>
            <p className="text-xs text-muted-foreground">Institutional-grade portfolio analysis and reporting</p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-sm text-muted-foreground animate-fade-in">
          <p>© 2024 Fargason Capital. Professional investment advisory services.</p>
        </div>
      </div>
    </div>
  )
}
