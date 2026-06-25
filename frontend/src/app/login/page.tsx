'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { useStore } from '@/lib/store'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { setUser, setToken } = useStore()

  const handleLogin = async () => {
    if (!email || !password) return toast.error('Fill all fields')
    setLoading(true)
    try {
      const res = await api.post('/api/auth/login', { email, password })
      setToken(res.data.token)
      setUser(res.data.user)
      toast.success('Welcome back!')
      router.push('/dashboard')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Login failed')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">CARLOS</h1>
          <p className="text-slate-400 mt-1">Telegram CRM Dashboard</p>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-slate-400 text-sm mb-1 block">Email</label>
            <input className="input" type="email" placeholder="your@email.com"
              value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="text-slate-400 text-sm mb-1 block">Password</label>
            <input className="input" type="password" placeholder="••••••••"
              value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()} />
          </div>
          <button className="btn-primary w-full mt-2" onClick={handleLogin} disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </div>
      </div>
    </div>
  )
}
