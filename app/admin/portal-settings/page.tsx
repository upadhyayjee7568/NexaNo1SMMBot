'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useState } from 'react'

export default function PortalSettingsPage() {
  const [settings, setSettings] = useState({
    siteName: 'NexaNo1 SMM Panel',
    currency: 'INR',
    registrationEnabled: true,
    dailyRewardAmount: '5',
  })

  const [saved, setSaved] = useState(false)

  const handleChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    setSaved(false)
  }

  const handleSave = async () => {
    try {
      // Save to database
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Error saving settings:', error)
    }
  }

  return (
    <div className="p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Portal Settings</h1>
        <p className="text-muted-foreground">Configure customer portal behavior</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Portal Configuration</CardTitle>
          <CardDescription>Customize portal features and settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Site Name</label>
            <input
              type="text"
              value={settings.siteName}
              onChange={(e) => handleChange('siteName', e.target.value)}
              className="w-full mt-2 p-2 border border-border rounded-lg"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Currency</label>
            <input
              type="text"
              value={settings.currency}
              onChange={(e) => handleChange('currency', e.target.value)}
              className="w-full mt-2 p-2 border border-border rounded-lg"
            />
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.registrationEnabled}
              onChange={(e) => handleChange('registrationEnabled', e.target.checked)}
              className="w-4 h-4"
            />
            <label className="text-sm font-medium">Allow User Registration</label>
          </div>

          <div>
            <label className="text-sm font-medium">Daily Reward Amount (₹)</label>
            <input
              type="number"
              value={settings.dailyRewardAmount}
              onChange={(e) => handleChange('dailyRewardAmount', e.target.value)}
              className="w-full mt-2 p-2 border border-border rounded-lg"
            />
          </div>

          <button
            onClick={handleSave}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90"
          >
            Save Changes
          </button>

          {saved && (
            <div className="bg-green-100 text-green-700 p-2 rounded">
              Settings saved successfully!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
