import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppStateProvider } from './hooks/useAppState'
import { ThemeProvider } from './contexts/ThemeContext'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'
import './App.css'

function App() {
  return (
    <ThemeProvider>
      <AppStateProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AppStateProvider>
    </ThemeProvider>
  )
}

export default App

