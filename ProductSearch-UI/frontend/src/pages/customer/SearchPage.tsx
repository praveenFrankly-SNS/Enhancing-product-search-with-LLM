import { useEffect, useState, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { SearchBar } from '@/components/customer/SearchBar'
import { ProductCard } from '@/components/customer/ProductCard'
import { FilterSidebar } from '@/components/customer/FilterSidebar'
import { SearchMetaBar } from '@/components/customer/SearchMetaBar'
import { searchAPI } from '@/services/api'
import { useSearchStore } from '@/store/useSearchStore'
import {
  FunnelSimple,
  ArrowLeft,
  SpinnerGap,
  MagnifyingGlass,
  Sparkle
} from '@phosphor-icons/react'

export function SearchPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryParam = searchParams.get('q') || ''

  const { query, filters, page, pageSize, setQuery, setPage, setFilters, resetFilters } = useSearchStore()
  const [showFilters, setShowFilters] = useState(true)
  const [sortBy, setSortBy] = useState('relevant')

  // Sync URL param with store
  useEffect(() => {
    if (queryParam && queryParam !== query) {
      setQuery(queryParam)
    }
  }, [queryParam, query, setQuery])

  // Fetch search results
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['search', query, page, pageSize, filters],
    queryFn: () => searchAPI.search({ query, page, page_size: pageSize, filters }),
    enabled: !!query,
  })

  // Apply sorting client-side
  const sortedResults = useMemo(() => {
    if (!data?.results) return []
    const resultsCopy = [...data.results]

    if (sortBy === 'price-asc') {
      return resultsCopy.sort((a, b) => (a.price || 0) - (b.price || 0))
    }
    if (sortBy === 'price-desc') {
      return resultsCopy.sort((a, b) => (b.price || 0) - (a.price || 0))
    }
    if (sortBy === 'rating') {
      return resultsCopy.sort((a, b) => (b.avg_rating || 0) - (a.avg_rating || 0))
    }
    // Default: bge vector semantic score relevance
    return resultsCopy.sort((a, b) => (b.similarity_score || 0) - (a.similarity_score || 0))
  }, [data?.results, sortBy])

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
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Header Search bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-6">
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-xl hover:bg-slate-100 transition-all active:scale-95 text-slate-700"
            aria-label="Back to home"
          >
            <ArrowLeft size={20} weight="bold" />
          </button>

          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Sparkle size={16} weight="fill" className="text-white" />
            </div>
            <span className="font-extrabold text-slate-900 hidden sm:inline">ProductSearch</span>
          </div>

          <div className="flex-1 max-w-2xl">
            <SearchBar onSearch={handleSearch} size="sm" initialValue={queryParam} />
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`
              flex items-center gap-2 px-4 py-2 border rounded-xl font-bold text-sm transition-all active:scale-95
              ${showFilters
                ? 'bg-primary-50 border-primary-300 text-primary-700 shadow-sm'
                : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
              }
            `}
          >
            <FunnelSimple size={16} weight="bold" />
            <span>Filters</span>
          </button>
        </div>
      </header>

      {/* Main content grid */}
      <div className="flex-1 max-w-7xl mx-auto px-6 py-8 w-full flex flex-col md:flex-row gap-8">
        {/* Sidebar */}
        {showFilters && query && (
          <FilterSidebar
            filters={filters}
            onFilterChange={setFilters}
            onClear={resetFilters}
          />
        )}

        {/* Results pane */}
        <main className="flex-1 space-y-6">
          {!query ? (
            <EmptyState />
          ) : isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState error={error} />
          ) : (data && sortedResults.length > 0) ? (
            <div className="space-y-6">
              {/* Metadata Indicators */}
              <SearchMetaBar
                totalResults={data.total_results}
                processingTimeMs={data.metadata.processing_time_ms}
                cached={data.metadata.cached}
                query={query}
              />

              {/* Toolbar */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
                <div>
                  <h2 className="text-xl font-extrabold text-slate-900">
                    Search Results
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Showing {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, data.total_results)} of {data.total_results} results
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Sort by</span>
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="text-sm font-semibold bg-white border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-primary-400"
                    >
                      <option value="relevant">Most Relevant</option>
                      <option value="price-asc">Price: Low to High</option>
                      <option value="price-desc">Price: High to Low</option>
                      <option value="rating">Top Rated</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Product Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {sortedResults.map((product, idx) => (
                  <ProductCard
                    key={product.product_id}
                    product={product}
                    showScore
                    isBestMatch={idx === 0 && page === 1 && sortBy === 'relevant'}
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
            <NoResultsState query={query} onClearFilters={resetFilters} />
          )}
        </main>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-24 bg-white border border-slate-200 rounded-3xl">
      <MagnifyingGlass size={64} weight="thin" className="mx-auto text-slate-300 mb-4" />
      <h3 className="text-xl font-bold text-slate-800 mb-1">
        Start Your Search
      </h3>
      <p className="text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
        Describe what you're looking for above. Our semantic search will match concepts and attributes instantly.
      </p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-center py-16 bg-white border border-slate-200 rounded-3xl">
        <SpinnerGap size={40} className="text-primary-600 animate-spin" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-white border border-slate-100 rounded-2xl overflow-hidden shadow-sm animate-pulse">
            <div className="aspect-square bg-slate-100" />
            <div className="p-4 space-y-3">
              <div className="h-3.5 bg-slate-100 rounded w-3/4" />
              <div className="h-3 bg-slate-100 rounded w-1/2" />
              <div className="h-5 bg-slate-100 rounded w-1/3 mt-4" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ErrorState({ error }: { error: any }) {
  return (
    <div className="text-center py-20 bg-white border border-red-100 rounded-3xl">
      <span className="text-4xl">⚠️</span>
      <h3 className="text-lg font-bold text-slate-800 mt-3 mb-1">
        Search Request Failed
      </h3>
      <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed mb-6">
        {error?.message || 'We ran into an issue connecting to Databricks Vector Search.'}
      </p>
      <button
        onClick={() => window.location.reload()}
        className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-bold rounded-xl transition-all active:scale-95 text-sm"
      >
        Try Again
      </button>
    </div>
  )
}

function NoResultsState({ query, onClearFilters }: { query: string; onClearFilters: () => void }) {
  return (
    <div className="text-center py-20 bg-white border border-slate-200 rounded-3xl space-y-6">
      <div className="text-5xl">🔍</div>
      <div className="space-y-1">
        <h3 className="text-xl font-bold text-slate-800">
          No Results Found
        </h3>
        <p className="text-sm text-slate-500 max-w-sm mx-auto">
          We couldn't find any products matching "{query}"
        </p>
      </div>
      <div className="inline-flex flex-col sm:flex-row gap-3 pt-2">
        <button
          onClick={onClearFilters}
          className="px-5 py-2.5 bg-primary-50 text-primary-700 hover:bg-primary-100 border border-primary-200 font-bold rounded-xl text-sm transition-all active:scale-95"
        >
          Clear Active Filters
        </button>
        <button
          onClick={() => window.history.back()}
          className="px-5 py-2.5 bg-white text-slate-700 hover:bg-slate-50 border border-slate-200 font-bold rounded-xl text-sm transition-all active:scale-95"
        >
          Go Back
        </button>
      </div>
      <div className="border-t border-slate-100 pt-6 max-w-md mx-auto space-y-2 text-xs text-slate-400 font-semibold text-left px-6">
        <p className="uppercase tracking-wider">Search Tips:</p>
        <ul className="list-disc list-inside space-y-1 font-medium text-slate-500">
          <li>Check for typos or misspelled brands.</li>
          <li>Remove price limits or category constraints.</li>
          <li>Try broader keywords like "chair" instead of "back pain ergonomic black mesh chair".</li>
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
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      if (currentPage > 3) pages.push('...')
      for (let i = Math.max(2, currentPage - 1); i <= Math.min(currentPage + 1, totalPages - 1); i++) {
        pages.push(i)
      }
      if (currentPage < totalPages - 2) pages.push('...')
      pages.push(totalPages)
    }
    return pages
  }

  return (
    <div className="flex items-center justify-center gap-2 border-t border-slate-100 pt-8 mt-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-4 py-2 text-sm font-semibold border border-slate-200 hover:border-primary-400 rounded-xl hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
      >
        Previous
      </button>

      {getPageNumbers().map((pageNum, idx) => (
        <button
          key={idx}
          onClick={() => typeof pageNum === 'number' && onPageChange(pageNum)}
          disabled={pageNum === '...'}
          className={`
            px-4 py-2 text-sm font-semibold border rounded-xl transition-all active:scale-95
            ${pageNum === currentPage
              ? 'bg-primary-600 text-white border-primary-600 shadow-md shadow-primary-200'
              : 'border-slate-200 hover:border-primary-400 hover:bg-slate-50'
            }
            ${pageNum === '...' ? 'cursor-default border-transparent hover:bg-transparent' : ''}
          `}
        >
          {pageNum}
        </button>
      ))}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 text-sm font-semibold border border-slate-200 hover:border-primary-400 rounded-xl hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
      >
        Next
      </button>
    </div>
  )
}
