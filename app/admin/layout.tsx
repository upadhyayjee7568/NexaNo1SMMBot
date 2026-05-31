'use client'

import { useSession } from '@/lib/auth-client'
import { redirect } from 'next/navigation'
import { AdminSidebar } from '@/components/admin-sidebar'
import type { ReactNode } from 'react'

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { data: session, isLoading } = useSession()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (!session?.user || session?.user.email !== process.env.NEXT_PUBLIC_ADMIN_EMAIL) {
    redirect('/sign-in')
  }

  return (
    <div className="flex min-h-screen bg-background">
      <AdminSidebar />
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}
