'use client'

import Link from 'next/link'
import { useSession } from '@/lib/auth-client'
import { Zap, Users, TrendingUp, Shield } from 'lucide-react'

export default function HomePage() {
  const { data: session } = useSession()

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary">NexaNo1 SMM Panel</h1>
          <div className="flex gap-4">
            {session?.user ? (
              <>
                <Link href="/dashboard" className="text-foreground hover:text-primary">
                  Dashboard
                </Link>
                <Link href="/admin" className="text-foreground hover:text-primary">
                  Admin
                </Link>
              </>
            ) : (
              <>
                <Link href="/sign-in" className="text-foreground hover:text-primary">
                  Sign In
                </Link>
                <Link href="/sign-up" className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90">
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-5xl font-bold mb-4">Professional SMM Services</h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Grow your social media presence with our reliable and affordable SMM panel.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/sign-up" className="bg-primary text-primary-foreground px-8 py-3 rounded-lg hover:bg-primary/90 text-lg">
              Get Started
            </Link>
            <Link href="#features" className="border border-primary text-primary px-8 py-3 rounded-lg hover:bg-primary hover:text-primary-foreground text-lg">
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 bg-card">
        <div className="max-w-7xl mx-auto">
          <h3 className="text-3xl font-bold text-center mb-12">Why Choose Us</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: Zap, title: 'Fast Delivery', description: 'Quick service delivery' },
              { icon: Users, title: 'Best Prices', description: 'Most competitive rates' },
              { icon: TrendingUp, title: 'Real Results', description: 'Genuine engagement' },
              { icon: Shield, title: 'Safe & Secure', description: 'Your data is protected' },
            ].map(({ icon: Icon, title, description }) => (
              <div key={title} className="p-6 border border-border rounded-lg">
                <Icon className="w-8 h-8 text-primary mb-4" />
                <h4 className="font-bold text-lg mb-2">{title}</h4>
                <p className="text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-4">
        <div className="max-w-7xl mx-auto text-center text-muted-foreground">
          <p>&copy; 2024 NexaNo1 SMM Panel. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
