'use client'
import { useEffect, useState } from 'react'
import api from '@/lib/api'

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([])

  useEffect(() => {
    api.get('/api/campaigns/').then(r => setCampaigns(r.data)).catch(() => {})
    const interval = setInterval(() => {
      api.get('/api/campaigns/').then(r => setCampaigns(r.data)).catch(() => {})
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Campaigns</h1>
      <div className="space-y-4">
        {campaigns.length === 0 && <p className="text-slate-400">No campaigns yet.</p>}
        {campaigns.map((c: any) => (
          <div key={c.id} className="card">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <p className="text-white font-medium">{c.message?.slice(0, 80)}...</p>
                <p className="text-slate-400 text-xs mt-1">By {c.sent_by} • {new Date(c.created_at).toLocaleString()}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full font-medium ml-4 ${
                c.status === 'completed' ? 'bg-green-900 text-green-400' :
                c.status === 'running' ? 'bg-blue-900 text-blue-400' :
                c.status === 'failed' ? 'bg-red-900 text-red-400' :
                'bg-slate-700 text-slate-400'
              }`}>{c.status}</span>
            </div>
            <div className="w-full bg-[#0f172a] rounded-full h-2 mb-2">
              <div className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${c.total_chats ? ((c.sent_count + c.failed_count) / c.total_chats * 100) : 0}%` }} />
            </div>
            <div className="flex gap-4 text-xs">
              <span className="text-green-400">✅ {c.sent_count} sent</span>
              <span className="text-red-400">❌ {c.failed_count} failed</span>
              <span className="text-slate-400">Total: {c.total_chats}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
