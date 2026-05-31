'use client'

import { useSession } from '@/lib/auth-client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowUpRight, TrendingUp, Wallet, ShoppingCart } from 'lucide-react'

export default function DashboardPage() {
  const { data: session } = useSession()

  const stats = [
    {
      title: 'Total Orders',
      value: '24',
      icon: ShoppingCart,
      change: '+12% from last month',
      color: 'text-blue-600',
    },
    {
      title: 'Wallet Balance',
      value: '₹5,240',
      icon: Wallet,
      change: '+₹500 this week',
      color: 'text-green-600',
    },
    {
      title: 'Total Spent',
      value: '₹12,850',
      icon: TrendingUp,
      change: '+8% this month',
      color: 'text-purple-600',
    },
  ]

  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Welcome back, {session?.user.name}!</h1>
        <p className="text-muted-foreground">Here&apos;s your SMM dashboard overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {stats.map(({ title, value, icon: Icon, change, color }) => (
          <Card key={title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{title}</CardTitle>
              <Icon className={`w-4 h-4 ${color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{value}</div>
              <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                <ArrowUpRight className="w-3 h-3" />
                {change}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Orders */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Orders</CardTitle>
          <CardDescription>Your latest service orders</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No orders yet. Start by exploring our services!
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
