import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { SearchBar } from '@/components/customer/SearchBar'
import { ProductCard } from '@/components/customer/ProductCard'
import { searchAPI, SearchFilters } from '@/services/api'
import { useSearchStore } from '@/store/useSearchStore'
import { 
  FunnelSimple, 
  SortAscending, 
  ArrowLeft,
  SpinnerGap,
  MagnifyingGlass
} from '@phosphor-icons/react'

export function SearchPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryParam = searchParams.get('q') || ''
  
  const { query, filters, page, pageSize, setQuery, setPage } = useSearchStore()
  const [showFilters, setShowFilters] = useState(false)
  
  // Sync URL param with store
  useEffect(() => {
    if (queryParam && queryParam !== query) {
      setQuery(queryParam)
    }
  }, [queryParam, query, setQuery])
  
  // Fetch search results
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['search', query, page, pageSize, filters],
    queryFn: () => searchAPI.search({ query, page, pageSize, filters }),
    enabled: !!query,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
  
  const handleSearch = (newQuery: string) => {
    setQuery(newQuery)
    setPage(1)
    navigate(`/search?q=${encodeURIComponent(newQuery)}`)
  }
  
  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="
                p-2 rounded-lg hover:bg-gray-100
                transition-colors duration-200
                focus:outline-none focus:ring-2 focus:ring-primary-500
              "
              aria-label="Back to home"
            >
              <ArrowLeft size={24} weight="bold" />
            </button>
            
            <div className="flex-1 max-w-3xl">
              <SearchBar onSearch={handleSearch} size="md" />
            </div>
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="
                flex items-center gap-2 px-4 py-2
                bg-white border-2 border-gray-200 rounded-xl
                hover:border-primary-300 hover:bg-primary-50
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
              "
            >
              <FunnelSimple size={20} weight="bold" />
              <span className="hidden md:inline font-medium">Filters</span>
            </button>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {!query ? (
          // Empty State
          <EmptyState />
        ) : isLoading ? (
          // Loading State
          <LoadingState />
        ) : isError ? (
          // Error State
          <ErrorState error={error} />
        ) : data && data.results.length > 0 ? (
          // Results
          <div className="space-y-6">
            {/* Results Info */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  Search Results
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Found {data.total_results.toLocaleString()} products for "{query}"
                  {data.metadata.cached && (
                    <span className="ml-2 text-primary-600 font-medium">
                      (Cached)
                    </span>
                  )}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Search completed in {data.metadata.processing_time_ms}ms
                </p>
              </div>
              
              <button
                className="
                  flex items-center gap-2 px-4 py-2
                  bg-white border border-gray-200 rounded-xl
                  hover:border-primary-300
                  transition-all duration-200
                "
              >
                <SortAscending size={20} />
                <span className="hidden md:inline text-sm font-medium">Sort</span>
              </button>
            </div>
            
            {/* Products Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {data.results.map((product) => (
                <ProductCard 
                  key={product.product_id} 
                  product={product}
                  showScore
                />
              ))}
            </div>
            
            {/* Pagination */}
            {data.total_pages > 1 && (
              <Pagination
                currentPage={page}
                totalPages={data.total_pages}
                onPageChange={handlePageChange}
              />
            )}
          </div>
        ) : (
          // No Results
          <NoResultsState query={query} />
        )}
      </main>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-20">
      <MagnifyingGlass size={64} weight="thin" className="mx-auto text-gray-300 mb-4" />
      <h3 className="text-xl font-semibold text-gray-700 mb-2">
        Start Your Search
      </h3>
      <p className="text-gray-500">
        Enter a search query to find products
      </p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-center py-12">
        <SpinnerGap size={48} className="text-primary-500 animate-spin" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-white rounded-2xl overflow-hidden animate-pulse">
            <div className="aspect-square bg-gray-200" />
            <div className="p-4 space-y-3">
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="h-6 bg-gray-200 rounded w-1/3 mt-4" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ErrorState({ error }: { error: any }) {
  return (
    <div className="text-center py-20">
      <div className="text-red-500 mb-4">
        <span className="text-4xl">⚠️</span>
      </div>
      <h3 className="text-xl font-semibold text-gray-700 mb-2">
        Search Failed
      </h3>
      <p className="text-gray-500 mb-4">
        {error?.message || 'An error occurred while searching'}
      </p>
      <button
        onClick={() => window.location.reload()}
        className="px-6 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
      >
        Try Again
      </button>
    </div>
  )
}

function NoResultsState({ query }: { query: string }) {
  return (
    <div className="text-center py-20">
      <div className="text-6xl mb-4">🔍</div>
      <h3 className="text-2xl font-semibold text-gray-700 mb-2">
        No Results Found
      </h3>
      <p className="text-gray-500 mb-6">
        We couldn't find any products matching "{query}"
      </p>
      <div className="space-y-2 text-sm text-gray-600">
        <p>Try:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Using different keywords</li>
          <li>Being more general in your search</li>
          <li>Checking your spelling</li>
        </ul>
      </div>
    </div>
  )
}

function Pagination({ 
  currentPage, 
  totalPages, 
  onPageChange 
}: { 
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const showPages = 5
    
    if (totalPages <= showPages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      pages.push(1)
      
      if (currentPage > 3) {
        pages.push('...')
      }
      
      for (let i = Math.max(2, currentPage - 1); i <= Math.min(currentPage + 1, totalPages - 1); i++) {
        pages.push(i)
      }
      
      if (currentPage < totalPages - 2) {
        pages.push('...')
      }
      
      pages.push(totalPages)
    }
    
    return pages
  }
  
  return (
    <div className="flex items-center justify-center gap-2 mt-12">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="
          px-4 py-2 rounded-xl border border-gray-200
          hover:border-primary-300 hover:bg-primary-50
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-all duration-200
        "
      >
        Previous
      </button>
      
      {getPageNumbers().map((pageNum, index) => (
        <button
          key={index}
          onClick={() => typeof pageNum === 'number' && onPageChange(pageNum)}
          disabled={pageNum === '...'}
          className={`
            px-4 py-2 rounded-xl border
            transition-all duration-200
            ${pageNum === currentPage
              ? 'bg-primary-500 text-white border-primary-500'
              : 'border-gray-200 hover:border-primary-300 hover:bg-primary-50'
            }
            ${pageNum === '...' ? 'cursor-default border-transparent' : ''}
          `}
        >
          {pageNum}
        </button>
      ))}
      
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="
          px-4 py-2 rounded-xl border border-gray-200
          hover:border-primary-300 hover:bg-primary-50
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-all duration-200
        "
      >
        Next
      </button>
    </div>
  )
}
