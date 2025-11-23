import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ChatInterface from '../components/ChatInterface'
import { useAppState } from '../hooks/useAppState'
import './ChatPage.css'

export default function ChatPage() {
  const { isLoggedIn } = useAppState()
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is logged in, if not redirect to login
    // Note: Dark mode is managed by ThemeContext, not here
    if (!isLoggedIn) {
      navigate('/login', { replace: true })
    }
  }, [isLoggedIn, navigate])

  if (!isLoggedIn) {
    return null // Prevent flash of content before redirect
  }

  return (
    <div className="chat-page-container">
      <ChatInterface />
    </div>
  )
}

