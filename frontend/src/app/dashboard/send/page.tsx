'use client'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import { useStore } from '@/lib/store'
import toast from 'react-hot-toast'
import { Send, RefreshCw } from 'lucide-react'

export default function SendPage() {
  const { selectedAccount, user } = useStore()
  const [folders, setFolders] = useState<any[]>([])
  const [selectedFolder, setSelectedFolder] = useState<any>(null)
  const [chats, setChats] = useState<any[]>([])
  const [message, setMessage] = useState('')
  const [delay, setDelay] = useState(3)
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [progress, setProgress] = useState<any>(null)
  const [campaignId, setCampaignId] = useState<string | null>(null)
  const [templates, setTemplates] = useState<any[]>([])

  useEffect(() => {
    loadFolders()
    api.get('/api/templates/').then(r => setTemplates(r.data)).catch(() => {})
  }, [selectedAccount])

  useEffect(() => {
    let interval: any
    if (campaignId && sending) {
      interval = setInterval(async () => {
        try {
          const res = await api.get(`/api/campaigns/${campaignId}/progress`)
          setProgress(res.data)
          if (res.data.status === 'completed' || res.data.status === 'failed') {
            setSending(false)
            toast.success('Campaign completed!')
            clearInterval(interval)
          }
        } catch {}
      }, 2000)
    }
    return () => clearInterval(interval)
  }, [campaignId, sending])

  const loadFolders = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/api/folders/${selectedAccount}`)
      setFolders(res.data)
    } catch {
      toast.error('Connect account first from Dashboard')
    }
    setLoading(false)
  }

  const loadChats = async (folder: any) => {
    setSelectedFolder(folder)
    setLoading(true)
    try {
      const res = await api.get(`/api/folders/${selectedAccount}/${folder.id}/chats`)
      setChats(res.data.chats)
    } catch {
      toast.error('Failed to load chats')
    }
    setLoading(false)
  }

  const filteredChats = chats.filter(c => filter === 'all' || c.type === filter)

  const sendMessage = async () => {
    if (!message) return toast.error('Write a message first')
    if (!selectedFolder) return toast.error('Select a folder')
    if (filteredChats.length === 0) return toast.error('No chats found')
    setSending(true)
    try {
      const res = await api.post('/api/campaigns/send', {
        account_number: selectedAccount,
        folder_id: selectedFolder.id,
        message,
        chat_ids: filteredChats.map((c: any) => c.chat_id),
        delay_seconds: delay,
        sent_by: user?.name || 'admin'
      })
      setCampaignId(res.data.campaign_id)
      toast.success(`Sending to ${filteredChats.length} chats...`)
    } catch {
      toast.error('Failed to start campaign')
      setSending(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Send Message</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-white">Select Folder</h2>
              <button onClick={loadFolders} className="text-slate-400 hover:text-white">
                <RefreshCw size={16} />
              </button>
            </div>
            {loading ? <p className="text-slate-400 text-sm">Loading...</p> : (
              <div className="space-y-2">
                {folders.map((f: any) => (
                  <button key={f.id} onClick={() => loadChats(f)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all ${
                      selectedFolder?.id === f.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-[#0f172a] text-slate-300 hover:bg-[#334155]'
                    }`}>
                    📁 {f.title}
                  </button>
                ))}
                {folders.length === 0 && <p className="text-slate-400 text-sm">No folders found. Connect account first.</p>}
              </div>
            )}
          </div>

          {chats.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-white mb-3">Filter Chats</h2>
              <div className="flex flex-wrap gap-2 mb-3">
                {['all', 'personal', 'group', 'channel', 'bot'].map(t => (
                  <button key={t} onClick={() => setFilter(t)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                      filter === t ? 'bg-blue-600 text-white' : 'bg-[#0f172a] text-slate-400 hover:bg-[#334155]'
                    }`}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
              <p className="text-slate-400 text-sm">{filteredChats.length} chats selected</p>
              <div className="max-h-40 overflow-y-auto mt-2 space-y-1">
                {filteredChats.slice(0, 20).map((c: any) => (
                  <div key={c.chat_id} className="text-xs text-slate-300 px-2 py-1 bg-[#0f172a] rounded">
                    {c.name} <span className="text-slate-500">• {c.type}</span>
                  </div>
                ))}
                {filteredChats.length > 20 && <p className="text-slate-500 text-xs px-2">+{filteredChats.length - 20} more</p>}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="card">
            <h2 className="font-semibold text-white mb-3">Compose Message</h2>
            {templates.length > 0 && (
              <div className="mb-3">
                <label className="text-slate-400 text-xs mb-1 block">Load Template</label>
                <select className="input text-sm" onChange={e => {
                  const t = templates.find((t: any) => t.id === e.target.value)
                  if (t) setMessage(t.message)
                }}>
                  <option value="">Select template...</option>
                  {templates.map((t: any) => (
                    <option key={t.id} value={t.id}>{t.title}</option>
                  ))}
                </select>
              </div>
            )}
            <textarea
              className="input min-h-[150px] resize-none"
              placeholder="Type your message here..."
              value={message}
              onChange={e => setMessage(e.target.value)}
            />
            <div className="mt-3">
              <label className="text-slate-400 text-xs mb-1 block">Delay between messages (seconds)</label>
              <input type="number" className="input" value={delay} min={1} max={30}
                onChange={e => setDelay(Number(e.target.value))} />
            </div>
          </div>

          {progress && (
            <div className="card">
              <h2 className="font-semibold text-white mb-3">Sending Progress</h2>
              <div className="w-full bg-[#0f172a] rounded-full h-3 mb-2">
                <div className="bg-blue-600 h-3 rounded-full transition-all"
                  style={{ width: `${progress.progress_percent}%` }} />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-green-400">✅ {progress.sent} sent</span>
                <span className="text-slate-400">{progress.progress_percent}%</span>
                <span className="text-red-400">❌ {progress.failed} failed</span>
              </div>
              <p className="text-center text-slate-400 text-xs mt-2 capitalize">{progress.status}</p>
            </div>
          )}

          <button onClick={sendMessage} disabled={sending || !message || !selectedFolder}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
            <Send size={18} />
            {sending ? 'Sending...' : `Send to ${filteredChats.length} Chats`}
          </button>
        </div>
      </div>
    </div>
  )
}
