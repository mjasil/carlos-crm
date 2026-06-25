'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  useEffect(() => {
    const token = localStorage.getItem('carlos_token')
    if (token) router.push('/dashboard')
    else router.push('/login')
  }, [])
  return <div className="flex items-center justify-center h-screen">
    <div className="text-slate-400">Loading...</div>
  </div>
}
