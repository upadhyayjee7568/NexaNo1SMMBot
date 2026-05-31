'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, Users, ShoppingCart, BarChart3 } from 'lucide-react'

export default function AdminDashboard() {
  const stats = [
    { title: 'Total Users', value: '1,234', icon: Users, color: 'text-blue-600' },
    { title: 'Total Orders', value: '5,678', icon: ShoppingCart, color: 'text-green-600' },
    { title: 'Revenue', value: '₹2,34,560', icon: BarChart3, color: 'text-purple-600' },
    { title: 'System Health', value: '99.9%', icon: Activity, color: 'text-yellow-600' },
  ]

  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground">System overview and management</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {stats.map(({ title, value, icon: Icon, color }) => (
          <Card key={title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{title}</CardTitle>
              <Icon className={`w-4 h-4 ${color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest system events</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            System monitoring active
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
