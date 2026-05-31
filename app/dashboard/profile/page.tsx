'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useSession } from '@/lib/auth-client'

export default function ProfilePage() {
  const { data: session } = useSession()

  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Profile Settings</h1>
        <p className="text-muted-foreground">Manage your account information</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Name</label>
            <p className="text-lg mt-1">{session?.user.name}</p>
          </div>
          <div>
            <label className="text-sm font-medium">Email</label>
            <p className="text-lg mt-1">{session?.user.email}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Security</CardTitle>
          <CardDescription>Manage your account security</CardDescription>
        </CardHeader>
        <CardContent>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90">
            Change Password
          </button>
        </CardContent>
      </Card>
    </div>
  )
}
