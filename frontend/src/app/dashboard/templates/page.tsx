'use client'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { Plus, Trash2 } from 'lucide-react'

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<any[]>([])
  const [title, setTitle] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const load = () => api.get('/api/templates/').then(r => setTemplates(r.data)).catch(() => {})

  useEffect(() => { load() }, [])

  const create = async () => {
    if (!title || !message) return toast.error('Fill all fields')
    setLoading(true)
    try {
      await api.post('/api/templates/', { title, message })
      toast.success('Template saved!')
      setTitle('')
      setMessage('')
      load()
    } catch { toast.error('Failed to save') }
    setLoading(false)
  }

  const del = async (id: string) => {
    await api.delete(`/api/templates/${id}`)
    toast.success('Deleted')
    load()
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Message Templates</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold text-white mb-4">Create Template</h2>
          <div className="space-y-3">
            <input className="input" placeholder="Template name" value={title} onChange={e => setTitle(e.target.value)} />
            <textarea className="input min-h-[120px] resize-none" placeholder="Message content..."
              value={message} onChange={e => setMessage(e.target.value)} />
            <button className="btn-primary w-full flex items-center justify-center gap-2" onClick={create} disabled={loading}>
              <Plus size={16} /> Save Template
            </button>
          </div>
        </div>
        <div className="space-y-3">
          {templates.length === 0 && <p className="text-slate-400">No templates yet.</p>}
          {templates.map((t: any) => (
            <div key={t.id} className="card">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-white font-medium">{t.title}</p>
                  <p className="text-slate-400 text-sm mt-1">{t.message?.slice(0, 100)}...</p>
                </div>
                <button onClick={() => del(t.id)} className="text-red-400 hover:text-red-300 ml-3">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
