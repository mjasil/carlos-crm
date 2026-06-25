'use client'
import { useState } from 'react'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { UserPlus } from 'lucide-react'

export default function TeamPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('member')
  const [loading, setLoading] = useState(false)

  const create = async () => {
    if (!name || !email || !password) return toast.error('Fill all fields')
    setLoading(true)
    try {
      await api.post('/api/auth/register', { name, email, password, role })
      toast.success('Team member added!')
      setName(''); setEmail(''); setPassword('')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed')
    }
    setLoading(false)
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Team Management</h1>
      <div className="card max-w-md">
        <h2 className="font-semibold text-white mb-4">Add Team Member</h2>
        <div className="space-y-3">
          <input className="input" placeholder="Full name" value={name} onChange={e => setName(e.target.value)} />
          <input className="input" type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="input" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
          <select className="input" value={role} onChange={e => setRole(e.target.value)}>
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </select>
          <button className="btn-primary w-full flex items-center justify-center gap-2" onClick={create} disabled={loading}>
            <UserPlus size={16} /> Add Member
          </button>
        </div>
      </div>
    </div>
  )
}
