'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus } from 'lucide-react'

export default function AdminServicesPage() {
  return (
    <div className="p-4 md:p-8">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Service Management</h1>
          <p className="text-muted-foreground">Manage all SMM services</p>
        </div>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Service
        </button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Services Catalog</CardTitle>
          <CardDescription>All available services</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Service management interface loading...
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
