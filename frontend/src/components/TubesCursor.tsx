import { useEffect, useRef } from 'react'
import './TubesCursor.css'

export default function TubesCursor() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const tubesAppRef = useRef<any>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    let mounted = true

    async function initTubesCursor() {
      try {
        // Dynamic import from CDN - TypeScript doesn't support URL imports
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        const TubesCursorModule = await import(
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          'https://cdn.jsdelivr.net/npm/threejs-components@0.0.19/build/cursors/tubes1.min.js'
        )
        const TubesCursor =
          TubesCursorModule.default ||
          TubesCursorModule.TubesCursor ||
          TubesCursorModule

        if (typeof TubesCursor === 'function' && mounted) {
          tubesAppRef.current = TubesCursor(canvas, {
            tubes: {
              colors: ['#f967fb', '#53bc28', '#6958d5'],
              lights: {
                intensity: 200,
                colors: ['#83f36e', '#fe8a2e', '#ff008a', '#60aed5'],
              },
            },
          })
          console.log('Tubes Cursor initialized successfully')
        }
      } catch (error) {
        console.error('Failed to initialize Tubes Cursor:', error)
        // Fallback background
        if (mounted && canvas) {
          const ctx = canvas.getContext('2d')
          if (ctx) {
            canvas.width = window.innerWidth
            canvas.height = window.innerHeight
            const gradient = ctx.createRadialGradient(
              canvas.width / 2,
              canvas.height / 2,
              0,
              canvas.width / 2,
              canvas.height / 2,
              canvas.width
            )
            gradient.addColorStop(0, 'rgba(255, 255, 255, 0.03)')
            gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.01)')
            gradient.addColorStop(1, 'rgba(0, 0, 0, 0.95)')
            ctx.fillStyle = gradient
            ctx.fillRect(0, 0, canvas.width, canvas.height)
          }
        }
      }
    }

    initTubesCursor()

    const handleResize = () => {
      if (canvas && !tubesAppRef.current) {
        const ctx = canvas.getContext('2d')
        if (ctx) {
          canvas.width = window.innerWidth
          canvas.height = window.innerHeight
        }
      }
    }

    let resizeTimeout: NodeJS.Timeout
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout)
      resizeTimeout = setTimeout(handleResize, 250)
    })

    return () => {
      mounted = false
      window.removeEventListener('resize', handleResize)
      if (resizeTimeout) clearTimeout(resizeTimeout)
    }
  }, [])

  return <canvas id="tubes-canvas" ref={canvasRef} className="tubes-canvas" />
}

