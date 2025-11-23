import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppState } from '../hooks/useAppState'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card, CardHeader, CardTitle } from './ui/card'
import { Avatar, AvatarFallback } from './ui/avatar'
import { Badge } from './ui/badge'
import { ScrollArea } from './ui/scroll-area'
import { Hash, Users, Plus, RefreshCw, Settings, LogOut, X } from 'lucide-react'
import { cn } from '../lib/utils'
import SettingsPanel from './Settings'

interface SidebarProps {
  currentChannel: string | null
  currentPeer: string | null
  onChannelSelect: (channel: string | null) => void
  onPeerSelect: (peer: string | null) => void
}

export default function Sidebar({
  currentChannel,
  currentPeer,
  onChannelSelect,
  onPeerSelect,
}: SidebarProps) {
  const navigate = useNavigate()
  const { currentUser, channels, peers, refreshPeerList, joinChannel, leaveChannel, unreadCounts, messages, logout } = useAppState()
  const [activeTab, setActiveTab] = useState<'channels' | 'peers' | 'settings'>('channels')
  const [newChannelName, setNewChannelName] = useState('')
  
  // Get last message for preview
  const getLastMessage = (target: string) => {
    const targetMessages = messages[target] || []
    if (targetMessages.length === 0) return null
    return targetMessages[targetMessages.length - 1]
  }
  
  const formatMessagePreview = (message: string, maxLength: number = 30) => {
    if (message.length <= maxLength) return message
    return message.substring(0, maxLength) + '...'
  }

  useEffect(() => {
    if (activeTab === 'peers') {
      refreshPeerList()
    }
  }, [activeTab, refreshPeerList])

  useEffect(() => {
    const interval = setInterval(() => {
      refreshPeerList()
    }, 10000)
    return () => clearInterval(interval)
  }, [refreshPeerList])

  const handleJoinChannel = async () => {
    if (!newChannelName.trim()) return
    await joinChannel(newChannelName.trim())
    setNewChannelName('')
  }

  const handleSelectPeer = async (peer: { username: string; ip: string; port: number }) => {
    try {
      const response = await fetch(
        `http://${currentUser?.webpeerIp}:${currentUser?.webpeerPort}/connect-peer`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: currentUser?.username,
            peer_username: peer.username,
            peer_ip: peer.ip,
            peer_port: peer.port,
          }),
        }
      )

      const data = await response.json()
      if (data.status === 'success') {
        console.log(`Connected to ${peer.username} via P2P`)
      }
    } catch (error) {
      console.error('Failed to connect to peer:', error)
    }

    onPeerSelect(peer.username)
  }

  const handleLeaveChannel = async (channelName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm(`Leave channel #${channelName}?`)) {
      await leaveChannel(channelName)
      if (currentChannel === channelName) {
        onChannelSelect(null)
      }
    }
  }

  const handleLogout = async () => {
    try {
      // Call logout endpoint to clear cookie on server
      await fetch('/logout', {
        method: 'POST',
        credentials: 'include',
      })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear cookie on client side
      document.cookie = 'auth=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
      
      // Clear app state
      logout()
      
      // Clear localStorage (optional - keep theme preferences)
      // localStorage.removeItem('chat-theme')
      // localStorage.removeItem('chat-color-mode')
      
      // Navigate to login page using React Router
      navigate('/login', { replace: true })
    }
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div className="w-80 border-r bg-card flex flex-col h-full">
      {/* User Info Header */}
      <Card className="border-0 border-b rounded-none shadow-none">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback className="bg-primary text-primary-foreground">
                {getInitials(currentUser?.username || 'User')}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base font-semibold truncate">
                {currentUser?.username || 'User'}
              </CardTitle>
              <p className="text-xs text-muted-foreground truncate">
                127.0.0.1:{currentUser?.peerPort || 0}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="h-8 w-8 shrink-0"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'channels' | 'peers' | 'settings')} className="flex-1 flex flex-col">
        <div className="px-4 pt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="channels" className="flex items-center gap-2">
              <Hash className="h-4 w-4" />
              Channels
            </TabsTrigger>
            <TabsTrigger value="peers" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Peers
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Channels Tab */}
        <TabsContent value="channels" className="flex-1 flex flex-col m-0 mt-4">
          <ScrollArea className="flex-1 px-4">
            <div className="space-y-1">
              {channels.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No channels yet
                </div>
              ) : (
                channels.map((channel) => {
                  const unread = unreadCounts[channel] || 0
                  const lastMessage = getLastMessage(channel)
                  return (
                    <div
                      key={channel}
                      className="group relative"
                    >
                      <button
                        onClick={() => onChannelSelect(channel)}
                        className={cn(
                          "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                          "hover:bg-accent hover:text-accent-foreground",
                          currentChannel === channel
                            ? "bg-accent text-accent-foreground"
                            : "text-muted-foreground"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <Hash className="h-4 w-4 shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium truncate">{channel}</span>
                              {unread > 0 && (
                                <Badge variant="destructive" className="h-5 min-w-5 px-1.5 text-xs flex items-center justify-center shrink-0">
                                  {unread > 99 ? '99+' : unread}
                                </Badge>
                              )}
                            </div>
                            {lastMessage && (
                              <div className="text-xs text-muted-foreground truncate mt-0.5">
                                {formatMessagePreview(lastMessage.message)}
                              </div>
                            )}
                          </div>
                        </div>
                      </button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className={cn(
                          "absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity",
                          "hover:bg-destructive hover:text-destructive-foreground"
                        )}
                        onClick={(e) => handleLeaveChannel(channel, e)}
                        title="Leave channel"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  )
                })
              )}
            </div>
          </ScrollArea>
          <div className="p-4 border-t space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="Channel name"
                value={newChannelName}
                onChange={(e) => setNewChannelName(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleJoinChannel()
                  }
                }}
                className="flex-1"
              />
              <Button
                onClick={handleJoinChannel}
                size="icon"
                variant="outline"
                className="shrink-0"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <Button
              onClick={handleJoinChannel}
              className="w-full"
              size="sm"
              disabled={!newChannelName.trim()}
            >
              Join Channel
            </Button>
          </div>
        </TabsContent>

        {/* Peers Tab */}
        <TabsContent value="peers" className="flex-1 flex flex-col m-0 mt-4">
          <ScrollArea className="flex-1 px-4">
            <div className="space-y-1">
              {peers.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No peers available
                </div>
              ) : (
                peers.map((peer) => {
                  const unread = unreadCounts[peer.username] || 0
                  const lastMessage = getLastMessage(peer.username)
                  // Assume peers in list are online (they're actively registered)
                  const isOnline = true
                  return (
                    <button
                      key={peer.username}
                      onClick={() => handleSelectPeer(peer)}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                        "hover:bg-accent hover:text-accent-foreground",
                        currentPeer === peer.username
                          ? "bg-accent text-accent-foreground"
                          : "text-muted-foreground"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div className="relative shrink-0">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-secondary text-secondary-foreground text-xs">
                              {getInitials(peer.username)}
                            </AvatarFallback>
                          </Avatar>
                          {isOnline && (
                            <div className="absolute bottom-0 right-0 h-3 w-3 bg-green-500 border-2 border-card rounded-full" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <div className="font-medium truncate">{peer.username}</div>
                            {!isOnline && (
                              <span className="text-xs text-muted-foreground">(offline)</span>
                            )}
                          </div>
                          {lastMessage ? (
                            <div className="text-xs text-muted-foreground truncate mt-0.5">
                              {formatMessagePreview(lastMessage.message)}
                            </div>
                          ) : (
                            <div className="text-xs text-muted-foreground truncate">
                              {peer.ip}:{peer.port}
                            </div>
                          )}
                        </div>
                        {unread > 0 && (
                          <Badge variant="destructive" className="h-5 min-w-5 px-1.5 text-xs flex items-center justify-center shrink-0">
                            {unread > 99 ? '99+' : unread}
                          </Badge>
                        )}
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          </ScrollArea>
          <div className="p-4 border-t space-y-2">
            <Button
              onClick={refreshPeerList}
              variant="outline"
              className="w-full"
              size="sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Peers
            </Button>
            <div className="text-center">
              <Badge variant="secondary" className="text-xs">
                {peers.length} peer{peers.length !== 1 ? 's' : ''} online
              </Badge>
            </div>
          </div>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="flex-1 flex flex-col m-0 mt-4">
          <ScrollArea className="flex-1 px-4">
            <SettingsPanel />
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  )
}
