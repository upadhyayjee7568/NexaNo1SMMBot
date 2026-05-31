'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function TicketsPage() {
  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Support Tickets</h1>
        <p className="text-muted-foreground">Get help from our support team</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Open Tickets</CardTitle>
        </CardHeader>
        <CardContent>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90">
            Create New Ticket
          </button>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Ticket History</CardTitle>
          <CardDescription>Your previous support requests</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No tickets yet
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
