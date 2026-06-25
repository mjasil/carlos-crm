'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  
  useEffect(() => {
    try {
      const token = localStorage.getItem('carlos_token')
      if (token) {
        router.push('/dashboard')
      } else {
        router.push('/login')
      }
    } catch {
      router.push('/login')
    }
  }, [router])

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-2">CARLOS</h1>
        <p className="text-slate-400">Loading...</p>
      </div>
    </div>
  )
}
