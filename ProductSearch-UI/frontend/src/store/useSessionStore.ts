import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SessionState {
  sessionId: string
  customerId: string
  recentSearches: string[]
  recentViews: string[]
  cartProductIds: string[]

  setSessionId: (id: string) => void
  setCustomerId: (id: string) => void
  addSearch: (query: string) => void
  addView: (productId: string) => void
  addCartItem: (productId: string) => void
  removeCartItem: (productId: string) => void
  clearSession: () => void
}

function generateId(): string {
  return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      sessionId: generateId(),
      customerId: 'CUST-FRANK-001',
      recentSearches: [],
      recentViews: [],
      cartProductIds: [],

      setSessionId: (id) => set({ sessionId: id }),

      setCustomerId: (id) => set({ customerId: id }),

      addSearch: (query) =>
        set((state) => {
          const searches = [query, ...state.recentSearches.filter((s) => s !== query)].slice(0, 10)
          return { recentSearches: searches }
        }),

      addView: (productId) =>
        set((state) => {
          const views = [productId, ...state.recentViews.filter((v) => v !== productId)].slice(0, 20)
          return { recentViews: views }
        }),

      addCartItem: (productId) =>
        set((state) => {
          if (state.cartProductIds.includes(productId)) return state
          return { cartProductIds: [...state.cartProductIds, productId].slice(0, 20) }
        }),

      removeCartItem: (productId) =>
        set((state) => ({
          cartProductIds: state.cartProductIds.filter((id) => id !== productId),
        })),

      clearSession: () =>
        set({
          recentSearches: [],
          recentViews: [],
          cartProductIds: [],
        }),
    }),
    { name: 'product-search-session' }
  )
)
