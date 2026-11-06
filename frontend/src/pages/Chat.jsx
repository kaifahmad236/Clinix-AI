import React, { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { sendMessage, getSessionHistory } from '../api.js'
import MarkdownContent from '../components/MarkdownContent.jsx'

export default function Chat() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialSession = searchParams.get('session') || null

  const [sessionId, setSessionId] = useState(initialSession)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(!!initialSession)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (initialSession) {
      loadHistory(initialSession)
    }
  }, [initialSession])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadHistory = async (sid) => {
    setLoadingHistory(true)
    try {
      const res = await getSessionHistory(sid)
      setMessages(
        res.data.map((m) => ({
          role: m.role,
          content: m.content,
          agent_used: m.agent_used,
        }))
      )
    } catch {
      // session might not exist / belong to user — start fresh
    } finally {
      setLoadingHistory(false)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setSending(true)

    try {
      const res = await sendMessage(text, sessionId)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.data.reply,
          agent_used: res.data.agent_used,
          citations: res.data.citations,
        },
      ])
      if (!sessionId) {
        setSessionId(res.data.session_id)
        setSearchParams({ session: res.data.session_id })
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Sorry, something went wrong reaching the AI assistant. Please try again — ' +
            (err.response?.data?.detail || 'unknown error'),
        },
      ])
    } finally {
      setSending(false)
    }
  }

  const startNewChat = () => {
    setSessionId(null)
    setMessages([])
    setSearchParams({})
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 flex flex-col h-[calc(100vh-3.5rem)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800">Health Chat</h1>
          <p className="text-xs text-slate-500">RAG-enabled personal medical assistant</p>
        </div>
        <button
          onClick={startNewChat}
          className="text-sm px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-100 transition"
        >
          + New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto bg-white border border-slate-200 rounded-xl p-4 space-y-4">
        {loadingHistory && <p className="text-sm text-slate-400">Loading conversation...</p>}

        {!loadingHistory && messages.length === 0 && (
          <div className="text-center text-slate-400 mt-10 space-y-2">
            <p className="font-medium text-slate-600">Ask ClinixAI a health question to get started.</p>
            <p className="text-xs">
              Upload medical reports in <strong>Reports</strong> to ask specific questions about your lab results,
              test numbers, and doctor notes with direct source citations.
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div
              className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-brand-600 text-white rounded-br-sm whitespace-pre-wrap'
                  : 'bg-slate-100 text-slate-800 rounded-bl-sm shadow-sm'
              }`}
            >
              {m.role === 'user' ? (
                m.content
              ) : (
                <MarkdownContent content={m.content} />
              )}
            </div>
            {m.role === 'assistant' && (m.agent_used === 'chat_agent+rag' || m.agent_used === 'chat_agent+clinical_kb') && (
              <span className="text-[10px] text-emerald-600 font-medium mt-1 ml-1 flex items-center gap-1">
                ✓ Grounded with verified clinical records
              </span>
            )}
          </div>
        ))}

        {sending && (
          <div className="flex justify-start">
            <div className="bg-slate-100 text-slate-500 rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm">
              ClinixAI is searching records & thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a health question or inquiry about your uploaded reports..."
          className="flex-1 px-4 py-2.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="bg-brand-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-brand-700 transition disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  )
}
