import { useNavigate } from 'react-router-dom'
import './BottomNav.css'

const TABS = [
  { id: 'home',     icon: '🏠', label: 'Home',     path: '/dashboard' },
  { id: 'courses',  icon: '📚', label: 'Courses',  path: '/courses'   },
  { id: 'progress', icon: '📊', label: 'Progress', path: '/progress'  },
  { id: 'ai',       icon: '🤖', label: 'AI Tutor', path: '/ai-tutor'  },
  { id: 'profile',  icon: '👤', label: 'Profile',  path: '/profile'   },
]

export default function BottomNav({ activeTab = 'home' }) {
  const navigate = useNavigate()

  return (
    <nav className="bottom-nav" role="navigation" aria-label="Main navigation">
      {TABS.map(tab => (
        <button
          key={tab.id}
          id={`nav-${tab.id}`}
          className={`bottom-nav-item ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => navigate(tab.path)}
          aria-label={tab.label}
          aria-current={activeTab === tab.id ? 'page' : undefined}
        >
          <span className="nav-icon">{tab.icon}</span>
          <span className="nav-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}
