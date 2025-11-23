import * as React from "react"
import { cn } from "../../lib/utils"

interface TooltipProps {
  children: React.ReactNode
  content: string
  side?: "top" | "bottom" | "left" | "right"
}

export function Tooltip({ children, content, side = "top" }: TooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false)

  const sideClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  }

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          className={cn(
            "absolute z-50 px-2 py-1 text-xs font-medium",
            "bg-popover text-popover-foreground border border-border",
            "whitespace-nowrap pointer-events-none",
            // Normal theme: rounded with shadow
            "rounded-md shadow-lg",
            // Neo-brutalism theme: sharp edges with offset shadow
            "[data-theme='neo-brutalism']:rounded-none [data-theme='neo-brutalism']:shadow-[4px_4px_0px_0px_hsl(var(--border))]",
            sideClasses[side]
          )}
        >
          {content}
          <div
            className={cn(
              "absolute w-2 h-2 bg-popover border border-border rotate-45",
              side === "top" && "top-full left-1/2 -translate-x-1/2 -translate-y-1/2 border-t-0 border-r-0",
              side === "bottom" && "bottom-full left-1/2 -translate-x-1/2 translate-y-1/2 border-b-0 border-l-0",
              side === "left" && "left-full top-1/2 -translate-y-1/2 -translate-x-1/2 border-l-0 border-b-0",
              side === "right" && "right-full top-1/2 -translate-y-1/2 translate-x-1/2 border-r-0 border-t-0"
            )}
          />
        </div>
      )}
    </div>
  )
}

