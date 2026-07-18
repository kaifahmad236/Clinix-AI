import React, { useEffect, useState } from 'react'
import { uploadReport, listReports, getReport } from '../api.js'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loadingList, setLoadingList] = useState(true)
  const [uploading, setUploading] = useState(false)
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

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 grid md:grid-cols-3 gap-6">
      <div className="md:col-span-1 space-y-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800 mb-2">Medical Reports</h1>
          <label className="block">
            <span className="sr-only">Upload PDF report</span>
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center hover:border-brand-500 transition cursor-pointer bg-white">
              <p className="text-sm font-medium text-slate-700">
                {uploading ? 'Uploading & summarizing...' : 'Click to upload a PDF report'}
              </p>
              <p className="text-xs text-slate-400 mt-1">PDF only, up to 15MB</p>
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
            <button
              key={r.id}
              onClick={() => openReport(r.id)}
              className={`w-full text-left px-4 py-3 rounded-xl border transition ${
                selected?.id === r.id
                  ? 'border-brand-500 bg-brand-50'
                  : 'border-slate-200 bg-white hover:bg-slate-50'
              }`}
            >
              <p className="text-sm font-medium text-slate-800 truncate">{r.filename}</p>
              <p className="text-xs text-slate-400">
                {new Date(r.created_at).toLocaleString()}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div className="md:col-span-2">
        {!selected && (
          <div className="h-full flex items-center justify-center text-slate-400 border border-slate-200 rounded-xl bg-white p-10 text-sm">
            Select or upload a report to view its AI summary.
          </div>
        )}
        {selected && (
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h2 className="font-semibold text-slate-800 mb-1">{selected.filename}</h2>
            <p className="text-xs text-slate-400 mb-4">
              {new Date(selected.created_at).toLocaleString()}
            </p>
            <div className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
              {selected.summary || 'No summary available.'}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
