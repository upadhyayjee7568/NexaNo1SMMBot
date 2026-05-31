'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function ServicesPage() {
  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Services</h1>
        <p className="text-muted-foreground">Browse and order our SMM services</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Available Services</CardTitle>
          <CardDescription>Loading services...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Services coming soon
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
