import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listSessions } from '../api.js'
import { useAuth } from '../AuthContext.jsx'

export default function Dashboard() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const { user } = useAuth()

  useEffect(() => {
    listSessions()
      .then((res) => setSessions(res.data))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-slate-800 mb-1">Welcome back, {user?.user_name}</h1>
      <p className="text-slate-500 text-sm mb-6">Here's a summary of your previous conversations.</p>

      <div className="flex gap-3 mb-6">
        <Link
          to="/chat"
          className="bg-brand-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-brand-700 transition"
        >
          + Start new chat
        </Link>
        <Link
          to="/reports"
          className="bg-white border border-slate-300 px-4 py-2 rounded-xl text-sm font-medium hover:bg-slate-100 transition"
        >
          Upload a report
        </Link>
      </div>

      {loading && <p className="text-sm text-slate-400">Loading...</p>}

      {!loading && sessions.length === 0 && (
        <div className="text-center text-slate-400 border border-dashed border-slate-300 rounded-xl p-10">
          No chats yet. Start a conversation to see it here.
        </div>
      )}

      <div className="space-y-2">
        {sessions.map((s) => (
          <Link
            key={s.session_id}
            to={`/chat?session=${s.session_id}`}
            className="block bg-white border border-slate-200 rounded-xl px-4 py-3 hover:bg-slate-50 transition"
          >
            <div className="flex justify-between items-start gap-4">
              <p className="text-sm text-slate-700 truncate flex-1">
                <span className="font-medium text-slate-500 mr-1">
                  {s.last_role === 'user' ? 'You:' : 'ClinixAI:'}
                </span>
                {s.last_message}
              </p>
              <span className="text-xs text-slate-400 whitespace-nowrap">
                {new Date(s.updated_at).toLocaleDateString()}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">{s.message_count} messages</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
