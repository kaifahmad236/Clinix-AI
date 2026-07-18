import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Navbar from './components/Navbar.jsx'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import Chat from './pages/Chat.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Reports from './pages/Reports.jsx'

function AppRoutes() {
  const { user } = useAuth()

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/signup" element={user ? <Navigate to="/dashboard" /> : <Signup />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <Reports />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to={user ? '/dashboard' : '/login'} />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
