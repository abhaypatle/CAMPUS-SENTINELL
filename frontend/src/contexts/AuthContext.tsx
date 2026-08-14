import React, { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../lib/api'

type User = {
  id: string
  name: string
  email: string
  role: 'REPORTER' | 'RESPONDER' | 'ADMIN'
}

type AuthContextType = {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(false)

  const isAuthenticated = !!user

  useEffect(() => {
    const token = localStorage.getItem('cs_token')
    if (token) {
      setLoading(true)
      api.get('/api/v1/auth/me', true)
        .then((data) => setUser(data))
        .catch(() => {
          localStorage.removeItem('cs_token')
          setUser(null)
        })
        .finally(() => setLoading(false))
    }
  }, [])

  const login = async (email: string, password: string) => {
    setLoading(true)
    try {
      const data = await api.post('/api/v1/auth/login', { email, password })
      const token = data.access_token
      localStorage.setItem('cs_token', token)
      const me = await api.get('/api/v1/auth/me', true)
      setUser(me)
    } finally {
      setLoading(false)
    }
  }

  const register = async (name: string, email: string, password: string) => {
    setLoading(true)
    try {
      await api.post('/api/v1/auth/register', { name, email, password })
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('cs_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
