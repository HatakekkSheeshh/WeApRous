import { useEffect, useRef, useState } from 'react'
import { useAppState } from '../hooks/useAppState'
import { ScrollArea } from './ui/scroll-area'
import { Avatar, AvatarFallback } from './ui/avatar'
import { Button } from './ui/button'
import { Tooltip } from './ui/tooltip'
import { ChevronDown } from 'lucide-react'
import { cn } from '../lib/utils'

interface MessageListProps {
  currentChannel: string | null
  currentPeer: string | null
  searchQuery?: string
}

export default function MessageList({ currentChannel, currentPeer, searchQuery = '' }: MessageListProps) {
  const { messages, currentUser } = useAppState()
  const containerRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)

  // Prioritize peer over channel
  const target = currentPeer || currentChannel
  let msgs = target ? messages[target] || [] : []
  
  // Filter messages by search query
  if (searchQuery.trim()) {
    const query = searchQuery.toLowerCase()
    msgs = msgs.filter(msg => 
      msg.message.toLowerCase().includes(query) ||
      msg.from.toLowerCase().includes(query)
    )
  }

  // Check if user is near bottom of scroll
  const checkScrollPosition = () => {
    if (scrollAreaRef.current) {
      const element = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement
      if (element) {
        const { scrollTop, scrollHeight, clientHeight } = element
        const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
        setShowScrollButton(!isNearBottom)
      }
    }
  }

  useEffect(() => {
    if (containerRef.current) {
      const scrollElement = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight
        checkScrollPosition()
      }
    }
  }, [msgs])

  useEffect(() => {
    const scrollElement = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement
    if (scrollElement) {
      scrollElement.addEventListener('scroll', checkScrollPosition)
      return () => scrollElement.removeEventListener('scroll', checkScrollPosition)
    }
  }, [target])

  const scrollToBottom = () => {
    const scrollElement = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement
    if (scrollElement) {
      scrollElement.scrollTo({ top: scrollElement.scrollHeight, behavior: 'smooth' })
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

  const formatTime = (timeString: string) => {
    const date = new Date(timeString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    if (days < 7) return `${days}d ago`
    return date.toLocaleDateString()
  }

  const formatFullTime = (timeString: string) => {
    const date = new Date(timeString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDate = (date: Date) => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
    const diff = today.getTime() - messageDate.getTime()
    const days = Math.floor(diff / 86400000)

    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return date.toLocaleDateString('en-US', { weekday: 'long' })
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const shouldShowDateSeparator = (currentMsg: { time: string }, prevMsg: { time: string } | null) => {
    if (!prevMsg) return true
    const currentDate = new Date(currentMsg.time)
    const prevDate = new Date(prevMsg.time)
    return (
      currentDate.getDate() !== prevDate.getDate() ||
      currentDate.getMonth() !== prevDate.getMonth() ||
      currentDate.getFullYear() !== prevDate.getFullYear()
    )
  }

  return (
    <div className="relative h-full">
      <ScrollArea className="h-full" ref={scrollAreaRef}>
        <div className="p-4 space-y-4" ref={containerRef}>
          {msgs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
              <div className="text-muted-foreground space-y-2">
                <p className="text-lg font-medium">No messages yet</p>
                <p className="text-sm">Start the conversation!</p>
              </div>
            </div>
          ) : (
            msgs.map((msg, index) => {
              const isSent = msg.from === currentUser?.username || msg.sent
              const showAvatar = index === 0 || msgs[index - 1].from !== msg.from
              const prevMsg = index > 0 ? msgs[index - 1] : null
              const showDateSeparator = shouldShowDateSeparator(msg, prevMsg)

              return (
                <div key={`${msg.time}-${index}`}>
                  {showDateSeparator && (
                    <div className="flex items-center justify-center my-4">
                      <div className="px-3 py-1 text-xs font-medium text-muted-foreground bg-muted/50 rounded-full">
                        {formatDate(new Date(msg.time))}
                      </div>
                    </div>
                  )}
                  <div
                    className={cn(
                      "flex gap-3",
                      isSent ? "justify-end" : "justify-start"
                    )}
                  >
                    {!isSent && showAvatar && (
                      <Avatar className="h-8 w-8 shrink-0">
                        <AvatarFallback className="bg-secondary text-secondary-foreground text-xs">
                          {getInitials(msg.from)}
                        </AvatarFallback>
                      </Avatar>
                    )}
                    {!isSent && !showAvatar && <div className="w-8" />}
                    <div
                      className={cn(
                        "flex flex-col gap-1 max-w-[70%]",
                        isSent && "items-end"
                      )}
                    >
                      {showAvatar && (
                        <div className="flex items-center gap-2 px-1">
                          <span className="text-xs font-medium text-foreground">
                            {msg.from}
                          </span>
                          <Tooltip content={formatFullTime(msg.time)} side="top">
                            <span className="text-xs text-muted-foreground cursor-help">
                              {formatTime(msg.time)}
                            </span>
                          </Tooltip>
                        </div>
                      )}
                      <div className="group relative">
                        <div
                          className={cn(
                            "rounded-lg px-4 py-2 text-sm",
                            isSent
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          {msg.message}
                        </div>
                      </div>
                    </div>
                    {isSent && showAvatar && (
                      <Avatar className="h-8 w-8 shrink-0">
                        <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                          {getInitials(currentUser?.username || 'You')}
                        </AvatarFallback>
                      </Avatar>
                    )}
                    {isSent && !showAvatar && <div className="w-8" />}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </ScrollArea>
      {showScrollButton && (
        <Button
          onClick={scrollToBottom}
          size="icon"
          className={cn(
            "absolute bottom-4 right-4 h-10 w-10 rounded-full shadow-lg z-10",
            "bg-primary text-primary-foreground hover:bg-primary/90"
          )}
        >
          <ChevronDown className="h-5 w-5" />
        </Button>
      )}
    </div>
  )
}
