import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Switch } from './ui/switch'
import { Settings as SettingsIcon, Palette, Moon, Sun, Bell, Volume2 } from 'lucide-react'

export default function Settings() {
  const { theme, colorMode, toggleTheme, toggleColorMode } = useTheme()
  const isNeoBrutalism = theme === 'neo-brutalism'
  const isDarkMode = colorMode === 'dark'
  
  const [soundEnabled, setSoundEnabled] = useState(() => {
    const saved = localStorage.getItem('chat-sound-enabled')
    return saved ? saved === 'true' : true
  })
  
  const [browserNotificationsEnabled, setBrowserNotificationsEnabled] = useState(() => {
    const saved = localStorage.getItem('chat-browser-notifications-enabled')
    return saved ? saved === 'true' : false
  })
  
  useEffect(() => {
    localStorage.setItem('chat-sound-enabled', soundEnabled.toString())
  }, [soundEnabled])
  
  useEffect(() => {
    localStorage.setItem('chat-browser-notifications-enabled', browserNotificationsEnabled.toString())
    
    if (browserNotificationsEnabled && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [browserNotificationsEnabled])

  return (
    <Card className="border-2">
      <CardHeader>
        <div className="flex items-center gap-2">
          <SettingsIcon className="h-5 w-5" />
          <CardTitle>Settings</CardTitle>
        </div>
        <CardDescription>Customize your chat experience</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isDarkMode ? (
              <Moon className="h-4 w-4 text-muted-foreground" />
            ) : (
              <Sun className="h-4 w-4 text-muted-foreground" />
            )}
            <div>
              <div className="font-medium">Dark Mode</div>
              <div className="text-sm text-muted-foreground">
                {isDarkMode ? 'Dark theme enabled' : 'Light theme enabled'}
              </div>
            </div>
          </div>
          <Switch
            checked={isDarkMode}
            onCheckedChange={() => toggleColorMode()}
          />
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Palette className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="font-medium">Neo-Brutalism Theme</div>
              <div className="text-sm text-muted-foreground">
                Bold colors, sharp edges, high contrast
              </div>
            </div>
          </div>
          <Switch
            checked={isNeoBrutalism}
            onCheckedChange={() => toggleTheme()}
          />
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Volume2 className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="font-medium">Sound Notifications</div>
              <div className="text-sm text-muted-foreground">
                Play sound when new messages arrive
              </div>
            </div>
          </div>
          <Switch
            checked={soundEnabled}
            onCheckedChange={setSoundEnabled}
          />
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="font-medium">Browser Notifications</div>
              <div className="text-sm text-muted-foreground">
                Show notifications when tab is inactive
              </div>
            </div>
          </div>
          <Switch
            checked={browserNotificationsEnabled}
            onCheckedChange={setBrowserNotificationsEnabled}
            disabled={!('Notification' in window)}
          />
        </div>
      </CardContent>
    </Card>
  )
}

