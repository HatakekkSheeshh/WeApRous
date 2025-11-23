import { useState, useEffect } from 'react'
import { useAppState } from '../hooks/useAppState'
import './LoginScreen.css'

interface LoginScreenProps {
  onLoginSuccess: () => void
}

export default function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const { registerPeer } = useAppState()
  const [showPeerForm, setShowPeerForm] = useState(false)
  const [sessionUsername, setSessionUsername] = useState('admin')
  const [sessionPassword, setSessionPassword] = useState('password')
  const [sessionMessage, setSessionMessage] = useState('')
  const [sessionMessageType, setSessionMessageType] = useState<'error' | 'success'>('error')

  const [username, setUsername] = useState('')
  const [trackerIp, setTrackerIp] = useState('127.0.0.1')
  const [trackerPort, setTrackerPort] = useState('8001')
  const [peerPort, setPeerPort] = useState('9100')
  const [webpeerIp, setWebpeerIp] = useState('127.0.0.1')
  const [webpeerPort, setWebpeerPort] = useState('8002')
  const [loginMessage, setLoginMessage] = useState('')
  const [loginMessageType, setLoginMessageType] = useState<'error' | 'success'>('error')

  useEffect(() => {
    // Check if cookie session exists
    const cookies = document.cookie.split(';')
    const hasAuthCookie = cookies.some((cookie) => cookie.trim().startsWith('auth=true'))

    if (hasAuthCookie) {
      setShowPeerForm(true)
    }
  }, [])

  const handleSessionLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setSessionMessage('')

    try {
      // Use relative URL - Vite proxy will forward to port 8080 (proxy server)
      // This ensures cookie session works correctly
      const response = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        credentials: 'include',
        body: `username=${encodeURIComponent(sessionUsername)}&password=${encodeURIComponent(sessionPassword)}`,
      })

      if (response.ok) {
        // Cookie is set, show peer registration form
        setShowPeerForm(true)
      } else {
        setSessionMessage('Invalid username or password')
        setSessionMessageType('error')
      }
    } catch (error) {
      setSessionMessage('Connection error: ' + error)
      setSessionMessageType('error')
    }
  }

  const handlePeerRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoginMessage('')

    if (!username) {
      setLoginMessage('Please enter your peer username')
      setLoginMessageType('error')
      return
    }

    try {
      await registerPeer({
        username,
        trackerIp,
        trackerPort: parseInt(trackerPort),
        peerPort: parseInt(peerPort),
        webpeerIp,
        webpeerPort: parseInt(webpeerPort),
      })
      onLoginSuccess()
    } catch (error: any) {
      setLoginMessage('Error: ' + error.message)
      setLoginMessageType('error')
      console.error('Peer registration error:', error)
    }
  }

  return (
    <div className="login-screen">
      <div className="login-box">
        <h2>Hybrid Chat App</h2>

        {!showPeerForm ? (
          <div id="cookieLoginForm">
            <form id="sessionLoginForm" onSubmit={handleSessionLogin}>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  id="sessionUsername"
                  value={sessionUsername}
                  onChange={(e) => setSessionUsername(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  id="sessionPassword"
                  value={sessionPassword}
                  onChange={(e) => setSessionPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn">
                Login
              </button>
              {sessionMessage && (
                <div className={sessionMessageType === 'error' ? 'error-message' : 'success-message'}>
                  {sessionMessage}
                </div>
              )}
            </form>
          </div>
        ) : (
          <div id="peerRegistrationForm">
            <h3>Register Peer</h3>
            <p>Enter your peer information to start chatting</p>
            <form id="peerForm" onSubmit={handlePeerRegister}>
              <div className="form-group">
                <label>Your Username (for P2P)</label>
                <input
                  type="text"
                  id="loginUsername"
                  placeholder="e.g., alice, bob"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
                <small>This is your peer identity, not the session login</small>
              </div>

              <div className="form-grid">
                <div className="form-group">
                  <label>Tracker Server IP</label>
                  <input
                    type="text"
                    id="trackerIp"
                    value={trackerIp}
                    onChange={(e) => setTrackerIp(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Tracker Server Port</label>
                  <input
                    type="number"
                    id="trackerPort"
                    value={trackerPort}
                    onChange={(e) => setTrackerPort(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Your P2P Port</label>
                <input
                  type="number"
                  id="peerPort"
                  value={peerPort}
                  onChange={(e) => setPeerPort(e.target.value)}
                  required
                />
                <small>Port for P2P TCP socket (must be unique per peer)</small>
              </div>

              <div className="form-grid">
                <div className="form-group">
                  <label>WebPeer Service IP</label>
                  <input
                    type="text"
                    id="webpeerIp"
                    value={webpeerIp}
                    onChange={(e) => setWebpeerIp(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>WebPeer Service Port</label>
                  <input
                    type="number"
                    id="webpeerPort"
                    value={webpeerPort}
                    onChange={(e) => setWebpeerPort(e.target.value)}
                    required
                  />
                </div>
              </div>
              <button type="submit" className="btn">
                Register & Start Chat
              </button>
              {loginMessage && (
                <div className={loginMessageType === 'error' ? 'error-message' : 'success-message'}>
                  {loginMessage}
                </div>
              )}
            </form>
          </div>
        )}
      </div>
    </div>
  )
}

