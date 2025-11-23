# Chat App Frontend - React + Vite

Frontend for the hybrid chat application built with React + TypeScript + Vite.

## Installation

```bash
cd frontend
npm install
```

## Development Server

```bash
npm run dev
```

The application will run at `http://localhost:5173`

## Production Build

```bash
npm run build
```

Build files will be generated in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ui/             # shadcn/ui components
│   │   ├── TubesCursor.tsx # Background canvas animation
│   │   ├── LoginScreen.tsx # Login page
│   │   ├── ChatInterface.tsx # Main chat interface
│   │   ├── ChatPage.tsx    # Chat page wrapper
│   │   ├── Sidebar.tsx     # Sidebar with channels, peers, and settings
│   │   ├── ChatArea.tsx    # Chat message area
│   │   ├── MessageList.tsx  # Message list component
│   │   ├── ChatInput.tsx   # Message input field
│   │   ├── EmojiPicker.tsx # Emoji picker component
│   │   └── Settings.tsx    # Settings panel
│   ├── pages/              # Page components
│   │   └── ChatPage.tsx    # Chat page
│   ├── hooks/
│   │   └── useAppState.tsx # Global state management and API calls
│   ├── contexts/
│   │   └── ThemeContext.tsx # Theme management (normal/neo-brutalism, light/dark)
│   ├── lib/
│   │   └── utils.ts        # Utility functions
│   ├── App.tsx             # Main app component with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles and theme variables
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Features

### Core Features
- ✅ Session-based login with cookies
- ✅ Peer registration with tracker server
- ✅ P2P connection via WebPeer service
- ✅ Channel chat (broadcast messaging)
- ✅ Direct peer-to-peer messaging
- ✅ Automatic peer list refresh
- ✅ Message polling every 2 seconds
- ✅ TubesCursor background animation
- ✅ Responsive design

### UI/UX Features
- ✅ Modern UI with shadcn/ui components
- ✅ Custom neo-brutalism theme
- ✅ Light/Dark mode toggle
- ✅ Theme persistence (localStorage)
- ✅ Smooth animations and transitions

### Chat Features (Group 1)
- ✅ Unread message count badges
- ✅ Scroll to bottom button
- ✅ Enhanced timestamps with tooltips
- ✅ Online/Offline status indicators
- ✅ Message date separators (Today, Yesterday, Date)
- ✅ Clear chat functionality
- ✅ Leave channel functionality
- ✅ Last message preview in sidebar

### Chat Features (Group 2)
- ✅ Typing indicators
- ✅ Message search/filtering
- ✅ Emoji picker for message input
- ✅ Keyboard shortcuts (Ctrl+K/Cmd+K for search, Esc to close)
- ✅ Sound notifications
- ✅ Browser notifications (when tab is inactive)

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - High-quality component library
- **Lucide React** - Icon library

## Configuration

### Vite Proxy

The development server is configured to proxy API requests:
- `/login` → `http://127.0.0.1:8080` (HTTP adapter)
- `/logout` → `http://127.0.0.1:8080` (HTTP adapter)
- `/api/*` → `http://127.0.0.1:8001` (Tracker server)

### Environment

- Frontend runs on port `5173`
- Backend tracker server on port `8001`
- WebPeer service on port `8002`
- HTTP adapter on port `8080`

## Development

### Adding New Components

Components are organized in `src/components/`:
- UI components (Button, Input, Card, etc.) are in `src/components/ui/`
- Feature components (ChatArea, Sidebar, etc.) are in `src/components/`
- Use shadcn/ui components for consistent styling

### State Management

Global state is managed in `src/hooks/useAppState.tsx`:
- User authentication
- Channels and peers
- Messages
- Unread counts
- Typing indicators
- Notifications

### Theming

Themes are managed in `src/contexts/ThemeContext.tsx`:
- Normal theme (default shadcn/ui styling)
- Neo-brutalism theme (custom bold design)
- Light/Dark mode support
- Theme preferences saved in localStorage

## Build & Deploy

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Notes

- The frontend communicates with multiple backend services (tracker, webpeer, httpadapter)
- All API calls use relative URLs that are proxied by Vite in development
- CORS is handled by the backend servers
- Session cookies are used for authentication
