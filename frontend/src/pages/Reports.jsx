import React, { useEffect, useState } from 'react'
import { uploadReport, listReports, getReport, deleteReport, reindexReports } from '../api.js'
import MarkdownContent from '../components/MarkdownContent.jsx'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loadingList, setLoadingList] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [reindexing, setReindexing] = useState(false)
  const [reindexMessage, setReindexMessage] = useState('')
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    refreshList()
  }, [])

  const refreshList = async () => {
    setLoadingList(true)
    try {
      const res = await listReports()
      setReports(res.data)
    } finally {
      setLoadingList(false)
    }
  }

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setError('')
    setUploading(true)
    try {
      const res = await uploadReport(file)
      setReports((prev) => [res.data, ...prev])
      setSelected(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try a different PDF.')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const openReport = async (id) => {
    const res = await getReport(id)
    setSelected(res.data)
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this report and remove its indexed vector data?')) return
    try {
      await deleteReport(id)
      setReports((prev) => prev.filter((r) => r.id !== id))
      if (selected?.id === id) {
        setSelected(null)
      }
    } catch (err) {
      setError('Failed to delete report.')
    }
  }

  const handleReindex = async () => {
    setReindexing(true)
    setReindexMessage('')
    setError('')
    try {
      const res = await reindexReports()
      setReindexMessage(res.data?.message || 'Reports re-indexed successfully.')
      setTimeout(() => setReindexMessage(''), 4000)
    } catch (err) {
      setError('Failed to sync reports into vector store.')
    } finally {
      setReindexing(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 grid md:grid-cols-3 gap-6">
      <div className="md:col-span-1 space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-xl font-bold text-slate-800">Medical Reports</h1>
            {reports.length > 0 && (
              <button
                onClick={handleReindex}
                disabled={reindexing}
                className="text-xs px-2.5 py-1 text-brand-600 bg-brand-50 border border-brand-200 rounded-lg hover:bg-brand-100 transition disabled:opacity-50"
                title="Sync and reindex all uploaded reports in the RAG vector store"
              >
                {reindexing ? 'Syncing...' : '⚡ Sync RAG'}
              </button>
            )}
          </div>

          {reindexMessage && (
            <p className="text-xs text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-lg p-2 mb-2">
              ✓ {reindexMessage}
            </p>
          )}

          <label className="block">
            <span className="sr-only">Upload PDF report</span>
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center hover:border-brand-500 transition cursor-pointer bg-white">
              <p className="text-sm font-medium text-slate-700">
                {uploading ? 'Uploading, chunking & indexing...' : 'Click to upload a PDF report'}
              </p>
              <p className="text-xs text-slate-400 mt-1">PDF only, up to 15MB • Auto-indexed for RAG</p>
              <input
                type="file"
                accept="application/pdf"
                onChange={handleFileChange}
                disabled={uploading}
                className="hidden"
              />
            </div>
          </label>
          {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
        </div>

        <div className="space-y-2">
          {loadingList && <p className="text-sm text-slate-400">Loading reports...</p>}
          {!loadingList && reports.length === 0 && (
            <p className="text-sm text-slate-400">No reports uploaded yet.</p>
          )}
          {reports.map((r) => (
            <div
              key={r.id}
              className={`flex items-center justify-between px-4 py-3 rounded-xl border transition ${
                selected?.id === r.id
                  ? 'border-brand-500 bg-brand-50'
                  : 'border-slate-200 bg-white hover:bg-slate-50'
              }`}
            >
              <button
                onClick={() => openReport(r.id)}
                className="flex-1 text-left min-w-0 pr-2"
              >
                <p className="text-sm font-medium text-slate-800 truncate">{r.filename}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-mono">
                    RAG Ready
                  </span>
                  <p className="text-xs text-slate-400">
                    {new Date(r.created_at).toLocaleDateString()}
                  </p>
                </div>
              </button>
              <button
                onClick={() => handleDelete(r.id)}
                className="text-slate-400 hover:text-red-500 p-1 text-xs transition"
                title="Delete report"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="md:col-span-2">
        {!selected && (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 border border-slate-200 rounded-xl bg-white p-10 text-sm space-y-2">
            <p className="font-medium text-slate-600">Select or upload a report to view its AI summary.</p>
            <p className="text-xs text-slate-400 text-center max-w-sm">
              All uploaded reports are vectorized into your private RAG collection so you can ask specific questions in Chat.
            </p>
          </div>
        )}
        {selected && (
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="font-semibold text-slate-800 text-lg mb-1">{selected.filename}</h2>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span>Uploaded: {new Date(selected.created_at).toLocaleString()}</span>
                  <span>•</span>
                  <span className="text-emerald-600 font-medium bg-emerald-50 px-2 py-0.5 rounded">
                    Indexed in RAG Vector Store
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleDelete(selected.id)}
                className="text-xs text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-lg transition"
              >
                Delete Report
              </button>
            </div>
            <div className="text-sm text-slate-700 leading-relaxed border-t border-slate-100 pt-4">
              <MarkdownContent content={selected.summary || 'No summary available.'} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
