'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { authClient } from '@/lib/auth-client'
import { useState } from 'react'
import { Menu, LogOut, Home, ShoppingCart, Wallet, MessageSquare, Settings, Users } from 'lucide-react'

export function Sidebar() {
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)

  const handleLogout = async () => {
    await authClient.signOut({ fetchOptions: { onSuccess: () => router.push('/sign-in') } })
  }

  const navItems = [
    { href: '/dashboard', icon: Home, label: 'Dashboard' },
    { href: '/dashboard/services', icon: ShoppingCart, label: 'Services' },
    { href: '/dashboard/orders', icon: ShoppingCart, label: 'Orders' },
    { href: '/dashboard/wallet', icon: Wallet, label: 'Wallet' },
    { href: '/dashboard/tickets', icon: MessageSquare, label: 'Support' },
    { href: '/dashboard/profile', icon: Settings, label: 'Profile' },
  ]

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-primary text-primary-foreground rounded-lg"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Sidebar */}
      <aside className={`fixed md:static top-0 left-0 h-screen w-64 bg-card border-r border-border transition-transform duration-300 z-40 ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        <div className="p-6 border-b border-border">
          <h1 className="text-2xl font-bold text-primary">NexaNo1</h1>
        </div>

        <nav className="p-4 space-y-2">
          {navItems.map(({ href, icon: Icon, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-secondary transition-colors"
            >
              <Icon className="w-5 h-5" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-4 left-4 right-4 border-t border-border pt-4">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-4 py-2 rounded-lg bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 md:hidden z-30"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  )
}
