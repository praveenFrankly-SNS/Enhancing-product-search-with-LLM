import axios, { AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Types
export interface SearchFilters {
  category?: string
  brand?: string
  min_price?: number
  max_price?: number
}

export interface SearchParams {
  query: string
  page?: number
  page_size?: number
  filters?: SearchFilters
  use_cache?: boolean
}

export interface Product {
  product_id: string
  product_name: string
  description: string | null
  brand: string | null
  category: string | null
  price: number | null
  currency: string
  attributes: Record<string, any> | null
  avg_rating: number | null
  review_count: number
  similarity_score: number | null
  image_url: string | null
}

export interface SearchMetadata {
  vector_search_time_ms: number
  product_fetch_time_ms: number
  processing_time_ms: number
  cached: boolean
  filters_applied: SearchFilters
}

export interface SearchResponse {
  query: string
  total_results: number
  page: number
  page_size: number
  total_pages: number
  results: Product[]
  metadata: SearchMetadata
}

export interface HealthStatus {
  status: string
  version: string
  environment: string
  services: Record<string, string>
}

export interface CacheStats {
  enabled: boolean
  connected_clients?: number
  used_memory?: string
  total_keys?: number
  hits?: number
  misses?: number
  hit_rate?: number
}

export interface TopQuery {
  query: string
  count: number
  avg_results: number
  avg_latency_ms: number
}

export interface SearchStats {
  cache: CacheStats
  top_queries: TopQuery[]
  analytics_period: string
}

// API methods
export const searchAPI = {
  // Search products
  search: async (params: SearchParams): Promise<SearchResponse> => {
    const { data } = await api.post<SearchResponse>('/api/v1/search/', params)
    return data
  },

  // Get search suggestions
  getSuggestions: async (query: string, limit = 5): Promise<string[]> => {
    const { data } = await api.get<{ partial_query: string; suggestions: string[] }>(
      '/api/v1/search/suggestions',
      { params: { q: query, limit } }
    )
    return data.suggestions
  },

  // Get product details
  getProduct: async (productId: string): Promise<Product> => {
    const { data } = await api.get<Product>(`/api/v1/products/${productId}`)
    return data
  },

  // Health check
  healthCheck: async (): Promise<HealthStatus> => {
    const { data } = await api.get<HealthStatus>('/api/v1/health/')
    return data
  },

  // Detailed health check
  detailedHealthCheck: async (): Promise<HealthStatus> => {
    const { data } = await api.get<HealthStatus>('/api/v1/health/detailed')
    return data
  },

  // Get statistics
  getStats: async (): Promise<SearchStats> => {
    const { data } = await api.get<SearchStats>('/api/v1/health/stats')
    return data
  },
}

export default api
