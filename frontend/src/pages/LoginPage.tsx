import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import TubesCursor from '../components/TubesCursor'
import LoginScreen from '../components/LoginScreen'
import { useAppState } from '../hooks/useAppState'
import '../components/LoginScreen.css'
import './LoginPage.css'

export default function LoginPage() {
  const { isLoggedIn } = useAppState()
  const navigate = useNavigate()

  useEffect(() => {
    // If already logged in, redirect to chat
    if (isLoggedIn) {
      navigate('/chat', { replace: true })
    }
  }, [isLoggedIn, navigate])

  const handleLoginSuccess = () => {
    // Navigate to chat page after successful login
    navigate('/chat', { replace: true })
  }

  return (
    <>
      <TubesCursor />
      <div className="login-page-container">
        <LoginScreen onLoginSuccess={handleLoginSuccess} />
      </div>
    </>
  )
}

