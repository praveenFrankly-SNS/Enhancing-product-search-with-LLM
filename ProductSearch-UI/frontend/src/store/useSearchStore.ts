import { create } from 'zustand'
import { SearchFilters } from '@/services/api'

interface SearchState {
  query: string
  filters: SearchFilters
  page: number
  pageSize: number
  
  // Actions
  setQuery: (query: string) => void
  setFilters: (filters: SearchFilters) => void
  setPage: (page: number) => void
  setPageSize: (pageSize: number) => void
  resetFilters: () => void
  reset: () => void
}

const initialFilters: SearchFilters = {}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  filters: initialFilters,
  page: 1,
  pageSize: 20,
  
  setQuery: (query) => set({ query, page: 1 }),
  
  setFilters: (filters) => set({ filters, page: 1 }),
  
  setPage: (page) => set({ page }),
  
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  
  resetFilters: () => set({ filters: initialFilters, page: 1 }),
  
  reset: () => set({
    query: '',
    filters: initialFilters,
    page: 1,
    pageSize: 20,
  }),
}))
