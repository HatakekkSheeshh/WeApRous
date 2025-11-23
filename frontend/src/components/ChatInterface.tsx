import { useState, useEffect } from 'react'
import Sidebar from './Sidebar'
import ChatArea from './ChatArea'

export default function ChatInterface() {
  const [currentChannel, setCurrentChannel] = useState<string | null>(null)
  const [currentPeer, setCurrentPeer] = useState<string | null>(null)
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K or Cmd+K: Focus search (if search is available)
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        // Search functionality will be handled by ChatArea
        const searchButton = document.querySelector('[title="Search messages"]') as HTMLElement
        if (searchButton) {
          searchButton.click()
        }
      }
      
      // Esc: Close modals/popovers
      if (e.key === 'Escape') {
        // Close any open popovers
        const popovers = document.querySelectorAll('[data-popover]')
        popovers.forEach(popover => {
          const closeButton = popover.querySelector('[aria-label="Close"]')
          if (closeButton) (closeButton as HTMLElement).click()
        })
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleChannelSelect = (channel: string | null) => {
    if (channel === null) {
      setCurrentChannel(null)
      return
    }
    // Toggle: if clicking the same channel, deselect it
    if (currentChannel === channel) {
      setCurrentChannel(null)
    } else {
      setCurrentChannel(channel)
      setCurrentPeer(null) // Clear peer when selecting channel
    }
  }

  const handlePeerSelect = (peer: string | null) => {
    if (peer === null) {
      setCurrentPeer(null)
      return
    }
    // Toggle: if clicking the same peer, deselect it
    if (currentPeer === peer) {
      setCurrentPeer(null)
    } else {
      setCurrentPeer(peer)
      setCurrentChannel(null) // Clear channel when selecting peer
    }
  }

  return (
    <div className="flex h-full w-full bg-background">
      <Sidebar
        currentChannel={currentChannel}
        currentPeer={currentPeer}
        onChannelSelect={handleChannelSelect}
        onPeerSelect={handlePeerSelect}
      />
      <ChatArea
        currentChannel={currentChannel}
        currentPeer={currentPeer}
      />
    </div>
  )
}

