'use client'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

export default function ContactsPage() {
  const [contacts, setContacts] = useState<any[]>([])
  const [search, setSearch] = useState('')

  useEffect(() => {
    api.get('/api/contacts/').then(r => setContacts(r.data)).catch(() => {})
  }, [])

  const filtered = contacts.filter(c =>
    c.name?.toLowerCase().includes(search.toLowerCase()) ||
    c.username?.toLowerCase().includes(search.toLowerCase())
  )

  const updateStatus = async (id: string, status: string) => {
    await api.put(`/api/contacts/${id}`, { status })
    setContacts(prev => prev.map(c => c.id === id ? { ...c, status } : c))
    toast.success('Updated!')
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Contacts</h1>
      <input className="input mb-4" placeholder="Search contacts..." value={search}
        onChange={e => setSearch(e.target.value)} />
      <div className="card">
        {filtered.length === 0 ? (
          <p className="text-slate-400">No contacts found. Send a campaign to sync contacts.</p>
        ) : (
          <div className="space-y-3">
            {filtered.map((c: any) => (
              <div key={c.id} className="flex items-center justify-between py-2 border-b border-[#334155]">
                <div>
                  <p className="text-white font-medium">{c.name}</p>
                  <p className="text-slate-400 text-xs">@{c.username} • {c.chat_type} • ₹{c.deposit_amount || 0}</p>
                </div>
                <select className="bg-[#0f172a] border border-[#334155] text-slate-300 text-xs rounded-lg px-2 py-1"
                  value={c.status} onChange={e => updateStatus(c.id, e.target.value)}>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="vip">VIP</option>
                </select>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
