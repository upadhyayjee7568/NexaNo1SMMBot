'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function ReportsPage() {
  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Reports & Analytics</h1>
        <p className="text-muted-foreground">System reports and insights</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Revenue Report</CardTitle>
            <CardDescription>Total revenue by time period</CardDescription>
          </CardHeader>
          <CardContent>
            <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90">
              Generate Report
            </button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User Report</CardTitle>
            <CardDescription>User statistics and growth</CardDescription>
          </CardHeader>
          <CardContent>
            <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90">
              Generate Report
            </button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Service Report</CardTitle>
            <CardDescription>Service usage analytics</CardDescription>
          </CardHeader>
          <CardContent>
            <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90">
              Generate Report
            </button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Audit Log</CardTitle>
            <CardDescription>System activity and changes</CardDescription>
          </CardHeader>
          <CardContent>
            <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90">
              View Logs
            </button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
