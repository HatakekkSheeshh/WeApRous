import { Button } from './ui/button'
import { Input } from './ui/input'
import { Send } from 'lucide-react'
import EmojiPicker from './EmojiPicker'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onKeyPress: (e: React.KeyboardEvent) => void
  disabled?: boolean
}

export default function ChatInput({ value, onChange, onSend, onKeyPress, disabled }: ChatInputProps) {
  const handleEmojiSelect = (emoji: string) => {
    onChange(value + emoji)
  }

  return (
    <div className="flex gap-2">
      <EmojiPicker onEmojiSelect={handleEmojiSelect} />
      <Input
        type="text"
        placeholder={disabled ? "Select a channel or peer to start chatting..." : "Type your message..."}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyPress={onKeyPress}
        disabled={disabled}
        className="flex-1"
      />
      <Button
        onClick={onSend}
        disabled={!value.trim() || disabled}
        size="icon"
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  )
}
