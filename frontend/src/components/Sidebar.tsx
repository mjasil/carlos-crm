'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useStore } from '@/lib/store'
import { LayoutDashboard, Send, Clock, Users, FileText, Settings, LogOut, MessageSquare } from 'lucide-react'
import clsx from 'clsx'

const links = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/send', label: 'Send Message', icon: Send },
  { href: '/dashboard/campaigns', label: 'Campaigns', icon: Clock },
  { href: '/dashboard/contacts', label: 'Contacts', icon: Users },
  { href: '/dashboard/templates', label: 'Templates', icon: FileText },
  { href: '/dashboard/team', label: 'Team', icon: Settings },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout, selectedAccount, setSelectedAccount } = useStore()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <div className="w-64 min-h-screen bg-[#1e293b] border-r border-[#334155] flex flex-col">
      <div className="p-6 border-b border-[#334155]">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <MessageSquare className="text-blue-500" size={22} />
          CARLOS CRM
        </h1>
        <p className="text-slate-400 text-xs mt-1">{user?.name || 'Admin'}</p>
      </div>

      <div className="p-4 border-b border-[#334155]">
        <p className="text-xs text-slate-400 mb-2">ACTIVE ACCOUNT</p>
        <div className="flex gap-2">
          {[1, 2].map(n => (
            <button key={n}
              onClick={() => setSelectedAccount(n)}
              className={clsx('flex-1 py-2 rounded-lg text-sm font-semibold transition-all',
                selectedAccount === n
                  ? 'bg-blue-600 text-white'
                  : 'bg-[#0f172a] text-slate-400 hover:bg-[#334155]'
              )}>
              Account {n}
            </button>
          ))}
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {links.map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href}
            className={clsx('flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all',
              pathname === href
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:bg-[#334155] hover:text-white'
            )}>
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-[#334155]">
        <button onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-[#334155] w-full transition-all">
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </div>
  )
}
