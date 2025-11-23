import { useState, useEffect, useRef } from 'react'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import { useAppState } from '../hooks/useAppState'
import { Card, CardHeader, CardTitle, CardDescription } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Hash, User, Trash2, Search, X } from 'lucide-react'
import { cn } from '../lib/utils'

interface ChatAreaProps {
  currentChannel: string | null
  currentPeer: string | null
}

export default function ChatArea({ currentChannel, currentPeer }: ChatAreaProps) {
  const { sendMessage, clearChat, markAsRead, typingUsers, setTyping, currentUser, messages } = useAppState()
  const [messageText, setMessageText] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  const target = currentPeer || currentChannel
  const targetMessages = target ? messages[target] || [] : []
  
  // Filter messages by search query
  const filteredMessages = searchQuery.trim()
    ? targetMessages.filter(msg => 
        msg.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        msg.from.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : targetMessages
  
  // Mark as read when viewing chat
  useEffect(() => {
    if (target) {
      markAsRead(target)
    }
  }, [target, markAsRead])

  const showNotification = (message: string) => {
    // Simple notification - can be replaced with toast component later
    const notification = document.createElement('div')
    notification.className = 'fixed top-4 right-4 bg-destructive text-destructive-foreground px-4 py-2 rounded-md shadow-lg z-50'
    notification.textContent = message
    document.body.appendChild(notification)

    setTimeout(() => {
      notification.remove()
    }, 3000)
  }

  const handleSend = async () => {
    if (!messageText.trim()) return
    if (!target) {
      showNotification('Select a channel or peer first!')
      return
    }

    setTyping(target, false) // Stop typing when sending

    try {
      await sendMessage(messageText.trim(), target, currentChannel !== null)
      setMessageText('')
    } catch (error) {
      showNotification('Error sending message')
      console.error('Error sending message:', error)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  const handleInputChange = (value: string) => {
    setMessageText(value)
    if (!target) return
    
    // Set typing indicator
    setTyping(target, true)
    
    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }
    
    // Stop typing after 3 seconds of inactivity
    typingTimeoutRef.current = setTimeout(() => {
      setTyping(target, false)
    }, 3000)
  }
  
  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [])
  
  // Get typing users for current target
  const typingUsersList = target ? Array.from(typingUsers[target] || []).filter(u => u !== currentUser?.username) : []

  // Prioritize peer over channel if both are set (shouldn't happen, but just in case)
  const isChannel = currentChannel !== null && currentPeer === null

  const handleClearChat = () => {
    if (!target) return
    if (confirm(`Clear all messages in ${isChannel ? `#${currentChannel}` : `chat with ${currentPeer}`}?`)) {
      clearChat(target)
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-background">
      {/* Chat Header */}
      <Card className="border-0 border-b rounded-none shadow-sm">
        <CardHeader className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isChannel ? (
                <Hash className="h-5 w-5 text-muted-foreground" />
              ) : (
                <User className="h-5 w-5 text-muted-foreground" />
              )}
              <div>
                <CardTitle className="text-lg">
                  {isChannel ? `#${currentChannel}` : currentPeer || 'Select a conversation'}
                </CardTitle>
                <CardDescription>
                  {isChannel ? 'Channel chat' : currentPeer ? 'Direct message' : 'Start chatting!'}
                </CardDescription>
              </div>
            </div>
            {target && (
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowSearch(!showSearch)}
                  className={cn("h-8 w-8", showSearch && "bg-accent")}
                  title="Search messages"
                >
                  <Search className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleClearChat}
                  className="h-8 w-8"
                  title="Clear chat"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
          
          {/* Search Bar */}
          {showSearch && target && (
            <div className="mt-4 flex items-center gap-2">
              <Input
                placeholder="Search messages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
                autoFocus
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  setSearchQuery('')
                  setShowSearch(false)
                }}
                className="h-8 w-8"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
          
          {showSearch && searchQuery.trim() && (
            <div className="mt-2 text-xs text-muted-foreground">
              Found {filteredMessages.length} message{filteredMessages.length !== 1 ? 's' : ''}
            </div>
          )}
        </CardHeader>
      </Card>

      {/* Messages */}
      <div className="flex-1 overflow-hidden">
        <MessageList 
          currentChannel={currentChannel} 
          currentPeer={currentPeer}
          searchQuery={showSearch ? searchQuery : ''}
        />
      </div>

      {/* Typing Indicator */}
      {typingUsersList.length > 0 && (
        <div className="px-4 py-2 text-xs text-muted-foreground italic border-t">
          {typingUsersList.length === 1 ? (
            <span>{typingUsersList[0]} is typing...</span>
          ) : typingUsersList.length === 2 ? (
            <span>{typingUsersList[0]} and {typingUsersList[1]} are typing...</span>
          ) : (
            <span>{typingUsersList[0]} and {typingUsersList.length - 1} others are typing...</span>
          )}
        </div>
      )}

      {/* Input */}
      <div className="border-t p-4">
        <ChatInput
          value={messageText}
          onChange={handleInputChange}
          onSend={handleSend}
          onKeyPress={handleKeyPress}
          disabled={!target}
        />
      </div>
    </div>
  )
}
