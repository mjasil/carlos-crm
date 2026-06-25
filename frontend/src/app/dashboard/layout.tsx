'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    try {
      const token = localStorage.getItem('carlos_token')
      if (!token) {
        router.push('/login')
      } else {
        setReady(true)
      }
    } catch {
      router.push('/login')
    }
  }, [router])

  if (!ready) return (
    <div className="flex items-center justify-center h-screen">
      <p className="text-slate-400">Loading...</p>
    </div>
  )

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}
