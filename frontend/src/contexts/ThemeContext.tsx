import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

type Theme = 'normal' | 'neo-brutalism'
type ColorMode = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  colorMode: ColorMode
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  setColorMode: (mode: ColorMode) => void
  toggleColorMode: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Load theme from localStorage or default to 'normal'
    const savedTheme = localStorage.getItem('chat-theme') as Theme
    return savedTheme || 'normal'
  })

  const [colorMode, setColorModeState] = useState<ColorMode>(() => {
    // Load color mode from localStorage or default to 'dark'
    const savedMode = localStorage.getItem('chat-color-mode') as ColorMode
    return savedMode || 'dark'
  })

  useEffect(() => {
    // Apply theme to document
    const html = document.documentElement
    if (theme === 'normal') {
      html.removeAttribute('data-theme')
    } else {
      html.setAttribute('data-theme', theme)
    }
    localStorage.setItem('chat-theme', theme)
  }, [theme])

  useEffect(() => {
    // Apply color mode to document
    const html = document.documentElement
    if (colorMode === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
    localStorage.setItem('chat-color-mode', colorMode)
  }, [colorMode])

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
  }

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'normal' ? 'neo-brutalism' : 'normal'))
  }

  const setColorMode = (mode: ColorMode) => {
    setColorModeState(mode)
  }

  const toggleColorMode = () => {
    setColorModeState((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  return (
    <ThemeContext.Provider value={{ theme, colorMode, setTheme, toggleTheme, setColorMode, toggleColorMode }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

