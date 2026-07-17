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
  Sparkle,
  GridFour,
  List,
} from '@phosphor-icons/react'
import { Globe, User, ShoppingCart, Lightbulb, Pencil, SlidersHorizontal } from 'lucide-react'

export function SearchPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryParam = searchParams.get('q') || ''

  const { query, filters, page, pageSize, setQuery, setPage, setFilters, resetFilters } = useSearchStore()
  const [showFilters, setShowFilters] = useState(true)
  const [sortBy, setSortBy] = useState('relevant')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  useEffect(() => {
    if (queryParam && queryParam !== query) {
      setQuery(queryParam)
    }
  }, [queryParam, query, setQuery])

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['search', query, page, pageSize, filters],
    queryFn: () => searchAPI.search({ query, page, page_size: pageSize, filters }),
    enabled: !!query,
  })

  const sortedResults = useMemo(() => {
    if (!data?.results) return []
    const copy = [...data.results]
    if (sortBy === 'price-asc') return copy.sort((a, b) => (a.price || 0) - (b.price || 0))
    if (sortBy === 'price-desc') return copy.sort((a, b) => (b.price || 0) - (a.price || 0))
    if (sortBy === 'rating') return copy.sort((a, b) => (b.avg_rating || 0) - (a.avg_rating || 0))
    return copy.sort((a, b) => (b.similarity_score || 0) - (a.similarity_score || 0))
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
      {/* ── Header ────────────────────────────────────────────────────── */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" className="text-white">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-extrabold text-slate-900 leading-none">ProductSearch</p>
              <p className="text-[9px] text-slate-400 font-semibold">Databricks Accelerator</p>
            </div>
          </div>

          {/* Nav */}
          <nav className="hidden lg:flex items-center gap-6 text-sm font-semibold text-slate-500 flex-shrink-0">
            <a href="/" className="hover:text-slate-900 transition-colors">Home</a>
            <a href="#about" className="hover:text-slate-900 transition-colors">About</a>
            <a href="#how-it-works" className="hover:text-slate-900 transition-colors">How it Works</a>
            <a href="#help" className="hover:text-slate-900 transition-colors">Help</a>
          </nav>

          {/* Search Bar — main */}
          <div className="flex-1 max-w-2xl mx-auto">
            <SearchBar onSearch={handleSearch} size="sm" initialValue={queryParam} />
          </div>

          {/* Filters toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`
              flex items-center gap-2 px-4 py-2 border rounded-xl font-bold text-sm transition-all active:scale-95 flex-shrink-0
              ${showFilters
                ? 'bg-blue-50 border-blue-300 text-blue-700 shadow-sm'
                : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
              }
            `}
          >
            <FunnelSimple size={16} weight="bold" />
            <span className="hidden sm:inline">Filters</span>
          </button>

          {/* Right icons */}
          <div className="hidden md:flex items-center gap-3 flex-shrink-0 text-slate-500">
            <button className="flex items-center gap-1.5 text-sm font-semibold hover:text-slate-900 transition-colors">
              <Globe size={16} />
              <span className="text-sm">English</span>
            </button>
            <button className="flex items-center gap-1.5 text-sm font-semibold hover:text-slate-900 transition-colors">
              <User size={16} />
              <span>Guest</span>
            </button>
            <button className="relative hover:text-slate-900 transition-colors">
              <ShoppingCart size={20} />
              <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-blue-600 text-white text-[9px] font-bold rounded-full flex items-center justify-center">2</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── Content ───────────────────────────────────────────────────── */}
      <div className="flex-1 max-w-7xl mx-auto px-6 py-8 w-full flex flex-col md:flex-row gap-8">
        {/* Sidebar */}
        {showFilters && query && (
          <aside>
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-slate-900 mb-5 transition-colors"
            >
              <ArrowLeft size={16} weight="bold" />
              <span>New Search</span>
            </button>
            <FilterSidebar
              filters={filters}
              onFilterChange={setFilters}
              onClear={resetFilters}
            />
          </aside>
        )}

        {/* Results */}
        <main className="flex-1 space-y-6 min-w-0">
          {!query ? (
            <EmptyState />
          ) : isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState error={error} />
          ) : data && sortedResults.length > 0 ? (
            <div className="space-y-5">
              {/* Results header + meta */}
              <div>
                <h2 className="text-2xl font-extrabold text-slate-900">Search Results</h2>
                <p className="text-sm text-slate-500 mt-0.5">
                  Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, data.total_results)} of{' '}
                  <span className="font-semibold">{data.total_results.toLocaleString()}</span> results for{' '}
                  <span className="text-blue-600 font-semibold">"{query}"</span>
                </p>
              </div>

              {/* SearchMetaBar — real Databricks LLM data */}
              <SearchMetaBar
                totalResults={data.total_results}
                processingTimeMs={data.metadata.processing_time_ms}
                cached={data.metadata.cached}
                query={query}
                rewrittenQuery={data.metadata.rewritten_query}
                intentTokens={data.metadata.intent_tokens ?? []}
                modelName={data.metadata.model_name}
              />

              {/* Toolbar */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-slate-400 uppercase tracking-wider">Sort by</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="text-sm font-semibold bg-white border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-blue-400"
                  >
                    <option value="relevant">Most Relevant</option>
                    <option value="price-asc">Price: Low to High</option>
                    <option value="price-desc">Price: High to Low</option>
                    <option value="rating">Top Rated</option>
                  </select>
                </div>
                {/* View mode toggle */}
                <div className="flex items-center gap-1.5 border border-slate-200 rounded-xl p-1 bg-white">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-1.5 rounded-lg transition-all ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-600'}`}
                  >
                    <GridFour size={18} weight="bold" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-1.5 rounded-lg transition-all ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-600'}`}
                  >
                    <List size={18} weight="bold" />
                  </button>
                </div>
              </div>

              {/* Product Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
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
            <NoResultsState query={query} />
          )}
        </main>
      </div>
    </div>
  )
}

// ── Sub-states ────────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="text-center py-24 bg-white border border-slate-200 rounded-3xl">
      <MagnifyingGlass size={64} weight="thin" className="mx-auto text-slate-300 mb-4" />
      <h3 className="text-xl font-bold text-slate-800 mb-1">Start Your Search</h3>
      <p className="text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
        Describe what you're looking for. Our AI-powered semantic search understands context and intent.
      </p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-center py-16 bg-white border border-slate-200 rounded-3xl">
        <div className="flex flex-col items-center gap-3">
          <SpinnerGap size={40} className="text-blue-600 animate-spin" />
          <p className="text-sm font-semibold text-slate-500">Querying Databricks Vector Search...</p>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
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
      <h3 className="text-lg font-bold text-slate-800 mt-3 mb-1">Search Request Failed</h3>
      <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed mb-6">
        {error?.message || 'We ran into an issue connecting to Databricks Vector Search.'}
      </p>
      <button
        onClick={() => window.location.reload()}
        className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all active:scale-95 text-sm"
      >
        Try Again
      </button>
    </div>
  )
}

// ── No Results — wireframe-accurate ──────────────────────────────────────────

function NoResultsState({ query }: { query: string }) {
  const SEARCH_TIPS = [
    { icon: <Lightbulb size={20} className="text-blue-500" />, bg: 'bg-blue-50', title: 'Use simpler keywords', desc: 'Use general terms to get broader results.' },
    { icon: <Pencil size={20} className="text-green-500" />, bg: 'bg-green-50', title: 'Check spelling', desc: 'Make sure all words are spelled correctly.' },
    { icon: <MagnifyingGlass size={20} weight="bold" className="text-purple-500" />, bg: 'bg-purple-50', title: 'Try different keywords', desc: 'Use synonyms or related words.' },
    { icon: <SlidersHorizontal size={20} className="text-amber-500" />, bg: 'bg-amber-50', title: 'Use fewer filters', desc: 'Remove some filters to see more results.' },
  ]

  // Generate related search suggestions from the query
  const queryWords = query.toLowerCase().split(' ').filter(w => w.length > 2)
  const suggestions = [
    queryWords.slice(0, 2).join(' '),
    queryWords[0] ? `${queryWords[0]} for home` : '',
    queryWords[0] ? `best ${queryWords[0]}` : '',
    queryWords.slice(-2).join(' '),
    queryWords[0] ? `${queryWords[0]} under budget` : '',
    queryWords[0] ? `affordable ${queryWords[0]}` : '',
  ].filter(Boolean).slice(0, 6)

  return (
    <div className="flex flex-col lg:flex-row gap-8 py-4">
      {/* Left: No results content */}
      <div className="flex-1 space-y-8">
        {/* Heading */}
        <div className="text-center space-y-3">
          <h2 className="text-3xl font-extrabold text-slate-900">No results found</h2>
          <p className="text-slate-500">
            We couldn't find any products matching your search{' '}
            <span className="text-blue-600 font-semibold">"{query}"</span>.
          </p>
        </div>

        {/* Illustration */}
        <div className="flex justify-center">
          <div className="relative w-64 h-48">
            <div className="absolute inset-0 bg-gradient-to-b from-blue-50 to-indigo-100 rounded-full blur-3xl opacity-40" />
            <div className="relative flex items-center justify-center h-full">
              <div className="w-32 h-32 bg-gradient-to-br from-blue-100 to-indigo-200 rounded-full flex items-center justify-center shadow-lg">
                <MagnifyingGlass size={56} weight="thin" className="text-blue-400" />
              </div>
            </div>
          </div>
        </div>

        {/* Search Tips */}
        <div>
          <h3 className="text-lg font-bold text-slate-900 mb-4">Search tips</h3>
          <div className="grid grid-cols-2 gap-4">
            {SEARCH_TIPS.map((tip, i) => (
              <div key={i} className="flex items-start gap-3 bg-white border border-slate-100 rounded-2xl p-4 shadow-sm">
                <div className={`w-10 h-10 ${tip.bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
                  {tip.icon}
                </div>
                <div>
                  <p className="font-bold text-sm text-slate-800">{tip.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{tip.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-center gap-2">
          <Sparkle size={16} className="text-blue-500" />
          <span className="text-sm text-slate-600">Still can't find what you're looking for?</span>
          <button className="text-sm font-bold text-blue-600 border border-blue-200 px-4 py-1.5 rounded-xl hover:bg-blue-50 transition-all">
            Contact Support
          </button>
        </div>
      </div>

      {/* Right: Try searching for */}
      <div className="w-full lg:w-72 flex-shrink-0">
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
          <h4 className="font-bold text-slate-900 text-sm">Try searching for</h4>
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => window.location.replace(`/search?q=${encodeURIComponent(s)}`)}
              className="w-full flex items-center gap-3 text-left py-2.5 px-3 rounded-xl hover:bg-slate-50 transition-colors group"
            >
              <MagnifyingGlass size={14} className="text-slate-400 flex-shrink-0" />
              <span className="text-sm text-slate-700 group-hover:text-blue-600 transition-colors">{s}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Pagination ────────────────────────────────────────────────────────────────

function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    if (totalPages <= 7) {
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
    <div className="flex items-center justify-between border-t border-slate-100 pt-6 mt-4">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold border border-slate-200 hover:border-blue-400 rounded-xl hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        ‹
      </button>

      <div className="flex items-center gap-1.5">
        {getPageNumbers().map((pageNum, idx) => (
          <button
            key={idx}
            onClick={() => typeof pageNum === 'number' && onPageChange(pageNum)}
            disabled={pageNum === '...'}
            className={`
              w-9 h-9 text-sm font-semibold rounded-xl transition-all
              ${pageNum === currentPage
                ? 'bg-blue-600 text-white shadow-md shadow-blue-200'
                : pageNum === '...'
                  ? 'cursor-default text-slate-400'
                  : 'border border-slate-200 hover:border-blue-400 hover:bg-slate-50 text-slate-700'
              }
            `}
          >
            {pageNum}
          </button>
        ))}
      </div>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold border border-slate-200 hover:border-blue-400 rounded-xl hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        ›
      </button>
    </div>
  )
}
