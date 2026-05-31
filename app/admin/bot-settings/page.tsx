'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useState } from 'react'

export default function BotSettingsPage() {
  const [settings, setSettings] = useState({
    welcomeMessage: 'Welcome to NexaNo1 SMM Panel Bot!',
    maintenanceMode: false,
    minDeposit: '50',
    referralBonus: '10',
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
        <h1 className="text-3xl font-bold">Bot Settings</h1>
        <p className="text-muted-foreground">Configure Telegram bot behavior</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Bot Configuration</CardTitle>
          <CardDescription>Customize bot messages and behavior</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Welcome Message</label>
            <textarea
              value={settings.welcomeMessage}
              onChange={(e) => handleChange('welcomeMessage', e.target.value)}
              className="w-full mt-2 p-2 border border-border rounded-lg"
              rows={3}
            />
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.maintenanceMode}
              onChange={(e) => handleChange('maintenanceMode', e.target.checked)}
              className="w-4 h-4"
            />
            <label className="text-sm font-medium">Maintenance Mode</label>
          </div>

          <div>
            <label className="text-sm font-medium">Minimum Deposit (₹)</label>
            <input
              type="number"
              value={settings.minDeposit}
              onChange={(e) => handleChange('minDeposit', e.target.value)}
              className="w-full mt-2 p-2 border border-border rounded-lg"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Referral Bonus (%)</label>
            <input
              type="number"
              value={settings.referralBonus}
              onChange={(e) => handleChange('referralBonus', e.target.value)}
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
