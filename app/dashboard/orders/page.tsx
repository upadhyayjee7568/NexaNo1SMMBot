'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function OrdersPage() {
  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Orders</h1>
        <p className="text-muted-foreground">Track and manage your orders</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Orders</CardTitle>
          <CardDescription>Recent order history</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No orders placed yet
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
