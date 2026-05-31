'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus } from 'lucide-react'

export default function AdminUsersPage() {
  return (
    <div className="p-4 md:p-8">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">User Management</h1>
          <p className="text-muted-foreground">Manage all registered users</p>
        </div>
        <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add User
        </button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Users List</CardTitle>
          <CardDescription>All registered users in the system</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            User management interface loading...
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
