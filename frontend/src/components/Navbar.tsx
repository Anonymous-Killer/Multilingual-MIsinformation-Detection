import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, Clock, ShieldCheck } from 'lucide-react'

function NavLink({ to, icon, label, active }: { to: string; icon: ReactNode; label: string; active: boolean }) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
        active ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
      }`}
    >
      {icon}
      {label}
    </Link>
  )
}

export function Navbar() {
  const { pathname } = useLocation()
  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <ShieldCheck size={16} className="text-white" strokeWidth={2.5} />
          </div>
          <span className="text-sm font-semibold text-gray-900">FactCheck AI</span>
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/" icon={<Home size={14} strokeWidth={2} />} label="Check" active={pathname === '/'} />
          <NavLink to="/history" icon={<Clock size={14} strokeWidth={2} />} label="History" active={pathname === '/history'} />
        </nav>
      </div>
    </header>
  )
}
