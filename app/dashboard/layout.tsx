'use client'

import { useSession } from '@/lib/auth-client'
import { redirect } from 'next/navigation'
import { Sidebar } from '@/components/sidebar'
import type { ReactNode } from 'react'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { data: session, isLoading } = useSession()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (!session?.user) {
    redirect('/sign-in')
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 md:ml-0">
        {children}
      </main>
    </div>
  )
}
