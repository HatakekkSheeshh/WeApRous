import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'

interface User {
  username: string
  trackerIp: string
  trackerPort: number
  peerPort: number
  webpeerIp: string
  webpeerPort: number
  token: string
}

interface Peer {
  username: string
  ip: string
  port: number
}

interface Message {
  from: string
  message: string
  time: string
  channel?: string
  sent?: boolean
  reactions?: Record<string, string[]> // {emoji: [usernames]}
}

interface AppStateContextType {
  currentUser: User | null
  isLoggedIn: boolean
  channels: string[]
  peers: Peer[]
  messages: Record<string, Message[]>
  unreadCounts: Record<string, number>
  lastReadPositions: Record<string, number>
  typingUsers: Record<string, Set<string>>
  loginSession: (username: string, password: string) => Promise<void>
  registerPeer: (peerInfo: Omit<User, 'token'>) => Promise<void>
  joinChannel: (channelName: string) => Promise<void>
  leaveChannel: (channelName: string) => Promise<void>
  refreshPeerList: () => Promise<void>
  sendMessage: (text: string, target: string, isChannel: boolean) => Promise<void>
  clearChat: (target: string) => void
  markAsRead: (target: string) => void
  logout: () => void
  setTyping: (target: string, isTyping: boolean) => void
}

const AppStateContext = createContext<AppStateContextType | undefined>(undefined)

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [channels, setChannels] = useState<string[]>([])
  const [peers, setPeers] = useState<Peer[]>([])
  const [messages, setMessages] = useState<Record<string, Message[]>>({})
  const [lastReadPositions, setLastReadPositions] = useState<Record<string, number>>({})
  const [typingUsers, setTypingUsers] = useState<Record<string, Set<string>>>({})
  const [messagePollInterval, setMessagePollInterval] = useState<NodeJS.Timeout | null>(null)
  
  // Sound notification
  const playNotificationSound = () => {
    const soundEnabled = localStorage.getItem('chat-sound-enabled') !== 'false'
    if (!soundEnabled) return
    
    try {
      // Create audio context for notification sound
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      oscillator.frequency.value = 800
      oscillator.type = 'sine'
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2)
      
      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.2)
    } catch (error) {
      console.error('Error playing notification sound:', error)
    }
  }
  
  // Browser notification
  const showBrowserNotification = (title: string, body: string) => {
    const notificationsEnabled = localStorage.getItem('chat-browser-notifications-enabled') === 'true'
    if (!notificationsEnabled || !('Notification' in window)) return
    
    if (Notification.permission === 'granted') {
      new Notification(title, {
        body,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
      })
    }
  }
  
  // Calculate unread counts
  const unreadCounts = React.useMemo(() => {
    const counts: Record<string, number> = {}
    Object.keys(messages).forEach((target) => {
      const targetMessages = messages[target] || []
      const lastRead = lastReadPositions[target] || 0
      const unread = targetMessages.filter((msg, index) => {
        const isSent = msg.from === currentUser?.username || msg.sent
        return !isSent && index >= lastRead
      }).length
      counts[target] = unread
    })
    return counts
  }, [messages, lastReadPositions, currentUser])

  const loginSession = useCallback(async (username: string, password: string) => {
    // Use relative URL - Vite proxy will forward to port 8080 (proxy server)
    // This ensures cookie session works correctly
    const response = await fetch('/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      credentials: 'include',
      body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
    })

    if (!response.ok) {
      throw new Error('Invalid username or password')
    }
  }, [])

  const initWebPeer = useCallback(async (user: User) => {
    const response = await fetch(`http://${user.webpeerIp}:${user.webpeerPort}/init-peer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: user.username,
        peer_ip: '127.0.0.1',
        peer_port: user.peerPort,
        tracker_ip: user.trackerIp,
        tracker_port: user.trackerPort,
      }),
    })

    const data = await response.json()
    if (data.status !== 'success') {
      throw new Error(data.message || 'Failed to initialize peer')
    }
  }, [])

  const registerPeerWithTracker = useCallback(async (user: User) => {
    const response = await fetch(`http://${user.trackerIp}:${user.trackerPort}/submit-info`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: user.username,
        ip: '127.0.0.1',
        port: user.peerPort,
        channels: channels,
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to register with tracker')
    }
  }, [channels])

  const registerPeer = useCallback(
    async (peerInfo: Omit<User, 'token'>) => {
      const user: User = { ...peerInfo, token: '' }
      await initWebPeer(user)
      await registerPeerWithTracker(user)
      setCurrentUser(user)
    },
    [initWebPeer, registerPeerWithTracker]
  )

  const joinChannel = useCallback(
    async (channelName: string) => {
      if (!currentUser) throw new Error('User not logged in')

      // Join channel via tracker
      const response = await fetch(
        `http://${currentUser.trackerIp}:${currentUser.trackerPort}/add-list`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: currentUser.username,
            channel: channelName,
          }),
        }
      )

      const data = await response.json()
      if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to join channel')
      }

      // Join channel via WebPeer
      const webpeerResponse = await fetch(
        `http://${currentUser.webpeerIp}:${currentUser.webpeerPort}/join-channel`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: currentUser.username,
            channel: channelName,
          }),
        }
      )

      const webpeerData = await webpeerResponse.json()
      if (webpeerData.status === 'success') {
        console.log('Auto-connected to peers in channel via P2P')
      }

      if (!channels.includes(channelName)) {
        setChannels((prev) => [...prev, channelName])
        setMessages((prev) => ({ ...prev, [channelName]: [] }))
        setLastReadPositions((prev) => ({ ...prev, [channelName]: 0 }))
      }
    },
    [currentUser, channels]
  )

  const leaveChannel = useCallback(
    async (channelName: string) => {
      if (!currentUser) throw new Error('User not logged in')

      // Leave channel via tracker
      try {
        const response = await fetch(
          `http://${currentUser.trackerIp}:${currentUser.trackerPort}/remove-list`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username: currentUser.username,
              channel: channelName,
            }),
          }
        )

        const data = await response.json()
        if (data.status === 'success') {
          setChannels((prev) => prev.filter((c) => c !== channelName))
          setMessages((prev) => {
            const newMessages = { ...prev }
            delete newMessages[channelName]
            return newMessages
          })
          setLastReadPositions((prev) => {
            const newPositions = { ...prev }
            delete newPositions[channelName]
            return newPositions
          })
        }
      } catch (error) {
        console.error('Failed to leave channel:', error)
      }
    },
    [currentUser]
  )

  const clearChat = useCallback((target: string) => {
    setMessages((prev) => ({ ...prev, [target]: [] }))
    setLastReadPositions((prev) => ({ ...prev, [target]: 0 }))
  }, [])

  const markAsRead = useCallback((target: string) => {
    const targetMessages = messages[target] || []
    setLastReadPositions((prev) => ({ ...prev, [target]: targetMessages.length }))
  }, [messages])

  const logout = useCallback(() => {
    // Clear all state
    setCurrentUser(null)
    setChannels([])
    setPeers([])
    setMessages({})
    setLastReadPositions({})
    setTypingUsers({})
    
    // Clear message polling interval
    if (messagePollInterval) {
      clearInterval(messagePollInterval)
      setMessagePollInterval(null)
    }
  }, [messagePollInterval])
  
  const setTyping = useCallback((target: string, isTyping: boolean) => {
    setTypingUsers((prev) => {
      const newTyping = { ...prev }
      if (!newTyping[target]) {
        newTyping[target] = new Set<string>()
      }
      
      if (isTyping) {
        newTyping[target].add(currentUser?.username || '')
      } else {
        newTyping[target].delete(currentUser?.username || '')
      }
      
      // Clean up empty sets
      if (newTyping[target].size === 0) {
        delete newTyping[target]
      }
      
      return newTyping
    })
  }, [currentUser])
  
  const refreshPeerList = useCallback(async () => {
    if (!currentUser) return

    try {
      const response = await fetch(
        `http://${currentUser.trackerIp}:${currentUser.trackerPort}/get-list`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        }
      )

      if (!response.ok) {
        console.error('Failed to refresh peers: HTTP', response.status)
        return
      }

      const data = await response.json()
      if (data.status === 'success') {
        setPeers(data.peers.filter((p: Peer) => p.username !== currentUser.username))
        if (data.channels) {
          setChannels(Object.keys(data.channels))
        }
      }
    } catch (error) {
      console.error('Failed to refresh peers:', error)
    }
  }, [currentUser])

  const sendMessage = useCallback(
    async (text: string, target: string, isChannel: boolean) => {
      if (!currentUser) throw new Error('User not logged in')

      // Add message to UI immediately
      setMessages((prev) => {
        const targetMessages = prev[target] || []
        return {
          ...prev,
          [target]: [
            ...targetMessages,
            {
              from: currentUser.username,
              message: text,
              time: new Date().toISOString(),
              sent: true,
              reactions: {},
            },
          ],
        }
      })

      try {
        if (!isChannel) {
          // Direct peer message
          const response = await fetch(
            `http://${currentUser.webpeerIp}:${currentUser.webpeerPort}/send-peer`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                username: currentUser.username,
                peer_username: target,
                message: text,
                channel: 'direct',
              }),
            }
          )

          const data = await response.json()
          if (data.status !== 'success') {
            console.error('Failed to send P2P message:', data.message)
          }
        } else {
          // Broadcast to channel
          const response = await fetch(
            `http://${currentUser.webpeerIp}:${currentUser.webpeerPort}/broadcast-peer`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                username: currentUser.username,
                message: text,
                channel: target,
              }),
            }
          )

          const data = await response.json()
          if (data.status === 'success') {
            console.log(`Broadcasted to ${data.sent_count} peers`)
          } else {
            console.error('Failed to broadcast:', data.message)
          }
        }
      } catch (error) {
        console.error('Error sending message:', error)
        throw error
      }
    },
    [currentUser]
  )

  // Start message polling
  useEffect(() => {
    if (!currentUser) {
      if (messagePollInterval) {
        clearInterval(messagePollInterval)
        setMessagePollInterval(null)
      }
      return
    }

    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `http://${currentUser.webpeerIp}:${currentUser.webpeerPort}/get-messages`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username: currentUser.username,
              channel: null,
            }),
          }
        )

        const data = await response.json()
        if (data.status === 'success' && data.messages) {
          setMessages((prev) => {
            const newMessages = { ...prev }
            data.messages.forEach((msg: Message) => {
              // For peer-to-peer messages (channel === 'direct'), use the peer's username as target
              // For channel messages, use channel name as target
              let target: string
              if (msg.channel === 'direct' || !msg.channel) {
                // Peer-to-peer message: target is the other peer's username
                // If message is from current user, we need to track which peer it was sent to
                // For now, if from current user, we'll skip it (already added when sending)
                // If from another peer, target is that peer's username
                if (msg.from === currentUser.username) {
                  // Skip messages sent by current user (already in UI)
                  return
                } else {
                  // Message from another peer - target is that peer's username
                  target = msg.from
                }
              } else {
                // Channel message - use channel name as target
                target = msg.channel
              }

              if (!target) {
                console.warn('Could not determine target for message:', msg)
                return
              }

              if (!newMessages[target]) {
                newMessages[target] = []
              }

              // Check if message already exists
              const existingMsgIndex = newMessages[target].findIndex(
                (m) => m.from === msg.from && m.message === msg.message && m.time === msg.time
              )

              if (existingMsgIndex === -1) {
                // New message - add it
                newMessages[target].push({
                  from: msg.from,
                  message: msg.message,
                  time: msg.time,
                  channel: msg.channel,
                  sent: msg.from === currentUser.username,
                  reactions: msg.reactions || {},
                })
                
                // Play sound and show notification for new messages (not from current user)
                if (msg.from !== currentUser.username) {
                  playNotificationSound()
                  
                  // Show browser notification if tab is not active
                  if (document.hidden) {
                    const isChannel = msg.channel && msg.channel !== 'direct'
                    const title = isChannel ? `#${target}` : msg.from
                    showBrowserNotification(title, msg.message)
                  }
                }
              }
            })
            return newMessages
          })
        }
      } catch (error) {
        console.error('Error polling messages:', error)
      }
    }, 2000)

    setMessagePollInterval(interval)

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [currentUser])

  // Connect to peer when selected (unused but kept for future use)
  // This function is available for future peer connection features
  // Uncomment when needed:
  /*
  const connectToPeer = useCallback(
    async (peer: Peer) => {
      if (!currentUser) return

      try {
        const response = await fetch(
          `http://${currentUser.webpeerIp}:${currentUser.webpeerPort}/connect-peer`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username: currentUser.username,
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
    },
    [currentUser]
  )
  */

  const value: AppStateContextType = {
    currentUser,
    isLoggedIn: currentUser !== null,
    channels,
    peers,
    messages,
    unreadCounts,
    lastReadPositions,
    typingUsers,
    loginSession,
    registerPeer,
    joinChannel,
    leaveChannel,
    refreshPeerList,
    sendMessage,
    clearChat,
    markAsRead,
    logout,
    setTyping,
  }

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>
}

export function useAppState() {
  const context = useContext(AppStateContext)
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppStateProvider')
  }
  return context
}

