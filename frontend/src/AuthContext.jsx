import React, { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('clinixai_user')
    return stored ? JSON.parse(stored) : null
  })

  const loginUser = (token, userData) => {
    localStorage.setItem('clinixai_token', token)
    localStorage.setItem('clinixai_user', JSON.stringify(userData))
    setUser(userData)
  }

  const logoutUser = () => {
    localStorage.removeItem('clinixai_token')
    localStorage.removeItem('clinixai_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loginUser, logoutUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
