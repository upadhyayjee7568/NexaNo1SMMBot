'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function WalletPage() {
  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Wallet</h1>
        <p className="text-muted-foreground">Manage your account balance</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Wallet Balance</CardTitle>
          <CardDescription>Current balance: ₹5,240</CardDescription>
        </CardHeader>
        <CardContent>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90">
            Add Funds
          </button>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No transactions yet
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
