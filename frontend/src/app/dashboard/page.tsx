'use client'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import { useStore } from '@/lib/store'
import { Send, Users, Clock, CheckCircle } from 'lucide-react'

export default function Dashboard() {
  const { selectedAccount } = useStore()
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [connected, setConnected] = useState(false)
  const [accountInfo, setAccountInfo] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get('/api/campaigns/').then(r => setCampaigns(r.data)).catch(() => {})
  }, [])

  const connectAccount = async () => {
    setLoading(true)
    try {
      const res = await api.post(`/api/accounts/connect/${selectedAccount}`)
      setAccountInfo(res.data)
      setConnected(true)
    } catch (e) {
      setConnected(false)
    }
    setLoading(false)
  }

  const totalSent = campaigns.reduce((a, c) => a + (c.sent_count || 0), 0)
  const totalFailed = campaigns.reduce((a, c) => a + (c.failed_count || 0), 0)
  const completed = campaigns.filter(c => c.status === 'completed').length

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 text-sm">Account {selectedAccount} active</p>
        </div>
        <button onClick={connectAccount} disabled={loading}
          className={`btn-primary text-sm ${connected ? 'bg-green-600' : ''}`}>
          {loading ? 'Connecting...' : connected ? `✅ ${accountInfo?.name}` : `Connect Account ${selectedAccount}`}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {[
          { label: 'Total Sent', value: totalSent, icon: Send, color: 'text-blue-400' },
          { label: 'Failed', value: totalFailed, icon: Users, color: 'text-red-400' },
          { label: 'Campaigns', value: campaigns.length, icon: Clock, color: 'text-yellow-400' },
          { label: 'Completed', value: completed, icon: CheckCircle, color: 'text-green-400' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card">
            <div className={`${color} mb-2`}><Icon size={20} /></div>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-slate-400 text-sm">{label}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Recent Campaigns</h2>
        {campaigns.length === 0 ? (
          <p className="text-slate-400 text-sm">No campaigns yet</p>
        ) : (
          <div className="space-y-3">
            {campaigns.slice(0, 5).map((c: any) => (
              <div key={c.id} className="flex items-center justify-between py-2 border-b border-[#334155]">
                <div>
                  <p className="text-white text-sm font-medium">{c.message?.slice(0, 40)}...</p>
                  <p className="text-slate-400 text-xs">Sent by {c.sent_by} • {c.sent_count}/{c.total_chats}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  c.status === 'completed' ? 'bg-green-900 text-green-400' :
                  c.status === 'running' ? 'bg-blue-900 text-blue-400' :
                  'bg-slate-700 text-slate-400'
                }`}>{c.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
