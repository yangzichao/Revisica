import { NavLink, Outlet } from 'react-router-dom'
import { FilePlus, ListTodo, Zap, FileSearch, Settings, HelpCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  to: string
  icon: LucideIcon
  label: string
  end?: boolean
}

const primaryNav: NavItem[] = [
  { to: '/', icon: FilePlus, label: 'New', end: true },
  { to: '/jobs', icon: ListTodo, label: 'Jobs' },
  { to: '/providers', icon: Zap, label: 'Providers' },
  { to: '/parse', icon: FileSearch, label: 'Parse' },
]

const secondaryNav: NavItem[] = [
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/help', icon: HelpCircle, label: 'Help' },
]

function SidebarLink({ to, icon: Icon, label, end }: NavItem): JSX.Element {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg mx-2',
          'text-sm font-medium transition-colors duration-150 no-drag',
          isActive
            ? 'bg-accent/10 text-accent'
            : 'text-ink-tertiary hover:text-ink-secondary hover:bg-paper-300/40',
        )
      }
    >
      <Icon size={18} strokeWidth={1.7} />
      <span>{label}</span>
    </NavLink>
  )
}

export default function Layout(): JSX.Element {
  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <nav className="w-52 flex flex-col shrink-0 bg-paper-200 border-r border-paper-300 select-none drag-region">
        {/* Brand */}
        <div className="h-14 flex items-center gap-2.5 px-5 no-drag">
          <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center shadow-subtle">
            <span className="font-serif text-sm font-bold text-white">R</span>
          </div>
          <span className="font-serif text-base font-semibold text-ink tracking-tight">
            Revisica
          </span>
        </div>

        {/* Primary navigation */}
        <div className="flex flex-col gap-0.5 mt-2 no-drag">
          {primaryNav.map((item) => (
            <SidebarLink key={item.to} {...item} />
          ))}
        </div>

        <div className="flex-1" />

        {/* Secondary navigation */}
        <div className="flex flex-col gap-0.5 pb-4 no-drag">
          {secondaryNav.map((item) => (
            <SidebarLink key={item.to} {...item} />
          ))}
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-hidden flex bg-paper-100">
        <Outlet />
      </main>
    </div>
  )
}
