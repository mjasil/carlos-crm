import { create } from 'zustand'

interface Store {
  user: any
  token: string | null
  selectedAccount: number
  setUser: (user: any) => void
  setToken: (token: string) => void
  setSelectedAccount: (n: number) => void
  logout: () => void
}

export const useStore = create<Store>((set) => ({
  user: null,
  token: null,
  selectedAccount: 1,
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('carlos_token', token)
    }
    set({ token })
  },
  setSelectedAccount: (n) => set({ selectedAccount: n }),
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('carlos_token')
    }
    set({ user: null, token: null })
  }
}))
