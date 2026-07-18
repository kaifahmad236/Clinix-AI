import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext.jsx'

export default function Navbar() {
  const { user, logoutUser } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  const handleLogout = () => {
    logoutUser()
    navigate('/login')
  }

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-14">
        <div className="flex items-center gap-6">
          <span className="font-bold text-brand-700 text-lg">ClinixAI</span>
          <div className="flex gap-1">
            <Link to="/dashboard" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100">
              Dashboard
            </Link>
            <Link to="/chat" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100">
              Chat
            </Link>
            <Link to="/reports" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100">
              Reports
            </Link>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500 hidden sm:inline">Hi, {user.user_name}</span>
          <button
            onClick={handleLogout}
            className="text-sm px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-100"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}
