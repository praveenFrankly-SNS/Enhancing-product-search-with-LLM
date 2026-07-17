import { useState, useRef, useEffect } from 'react'
import { MagnifyingGlass, X, ArrowRight, Lightbulb } from '@phosphor-icons/react'
import { searchAPI, SuggestionsResponse } from '@/services/api'
import { clsx } from 'clsx'

interface SearchBarProps {
  onSearch: (query: string) => void
  placeholder?: string
  autoFocus?: boolean
  size?: 'sm' | 'md' | 'lg'
  initialValue?: string
}

export function SearchBar({
  onSearch,
  placeholder = 'Search for anything…',
  autoFocus = false,
  size = 'md',
  initialValue = '',
}: SearchBarProps) {
  const [value, setValue] = useState(initialValue)
  const [suggestions, setSuggestions] = useState<SuggestionsResponse | null>(null)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus()
  }, [autoFocus])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Fetch suggestions from Databricks with 280ms debounce
  useEffect(() => {
    if (value.length < 2) {
      setSuggestions(null)
      return
    }
    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const result = await searchAPI.getSuggestions(value, 6)
        setSuggestions(result)
        setOpen(true)
      } catch {
        setSuggestions(null)
      } finally {
        setLoading(false)
      }
    }, 280)
    return () => clearTimeout(timer)
  }, [value])

  const handleSubmit = (q: string) => {
    if (!q.trim()) return
    setValue(q)
    setOpen(false)
    onSearch(q.trim())
  }

  // Highlight matched portion of suggestion text
  const highlightMatch = (text: string, query: string) => {
    if (!query) return <span>{text}</span>
    const idx = text.toLowerCase().indexOf(query.toLowerCase())
    if (idx === -1) return <span>{text}</span>
    return (
      <>
        {text.slice(0, idx)}
        <strong className="font-bold text-slate-900">{text.slice(idx, idx + query.length)}</strong>
        {text.slice(idx + query.length)}
      </>
    )
  }

  const hasResults = suggestions && (
    (suggestions.completions?.length ?? 0) > 0 ||
    (suggestions.categories?.length ?? 0) > 0 ||
    (suggestions.related_suggestions?.length ?? 0) > 0
  )

  return (
    <div ref={containerRef} className="relative w-full">
      <div
        className={clsx(
          'flex items-center gap-2 bg-white border-2 rounded-2xl transition-all duration-200',
          open || value
            ? 'border-primary-400 shadow-lg shadow-primary-100/50'
            : 'border-slate-200 hover:border-slate-300',
          size === 'lg' && 'px-5 py-4',
          size === 'md' && 'px-4 py-3',
          size === 'sm' && 'px-3 py-2',
        )}
      >
        <MagnifyingGlass
          size={size === 'lg' ? 22 : 18}
          weight="bold"
          className="text-slate-400 flex-shrink-0"
        />
        <input
          ref={inputRef}
          value={value}
          onChange={(e) => { setValue(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit(value)
            if (e.key === 'Escape') setOpen(false)
          }}
          placeholder={placeholder}
          className={clsx(
            'flex-1 bg-transparent outline-none text-slate-900 placeholder-slate-400',
            size === 'lg' && 'text-base',
            (size === 'md' || size === 'sm') && 'text-sm',
          )}
        />
        {value && (
          <button
            onClick={() => { setValue(''); setSuggestions(null); inputRef.current?.focus() }}
            className="p-1 rounded-full hover:bg-slate-100 transition-colors"
            aria-label="Clear search"
          >
            <X size={16} className="text-slate-400" />
          </button>
        )}
        <button
          id="search-submit-btn"
          onClick={() => handleSubmit(value)}
          className={clsx(
            'flex items-center gap-2 bg-primary-600 text-white font-semibold rounded-xl px-4 py-2',
            'hover:bg-primary-700 active:scale-95 transition-all duration-150',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          )}
        >
          <MagnifyingGlass size={16} weight="bold" />
          <span className={size === 'sm' ? 'hidden' : undefined}>Search</span>
        </button>
      </div>

      {/* Autocomplete Dropdown — Databricks-powered, wireframe-accurate */}
      {open && hasResults && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-2xl border border-slate-100 z-50 overflow-hidden">
          <div className="flex">
            {/* Left pane: Query completions + Categories */}
            <div className="flex-1 py-2 min-w-0">
              {/* Completions */}
              {(suggestions?.completions?.length ?? 0) > 0 && (
                <>
                  {suggestions!.completions.map((s, i) => (
                    <button
                      key={i}
                      onMouseDown={() => handleSubmit(s)}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-primary-50 hover:text-primary-700 transition-colors text-left group"
                    >
                      <MagnifyingGlass size={14} className="text-slate-400 flex-shrink-0" />
                      <span className="font-medium">{highlightMatch(s, value)}</span>
                      {i === 0 && (
                        <span className="ml-auto text-[10px] font-bold bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full flex-shrink-0">
                          Popular
                        </span>
                      )}
                    </button>
                  ))}
                </>
              )}

              {/* Categories section */}
              {(suggestions?.categories?.length ?? 0) > 0 && (
                <>
                  <div className="px-4 pt-3 pb-1">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Categories</p>
                  </div>
                  {suggestions!.categories.map((cat, i) => (
                    <button
                      key={i}
                      onMouseDown={() => handleSubmit(cat)}
                      className="w-full flex items-center justify-between px-4 py-2.5 text-sm text-slate-700 hover:bg-primary-50 hover:text-primary-700 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-slate-600 text-sm">
                          {getCategoryIcon(cat)}
                        </div>
                        <div className="text-left">
                          <p className="font-semibold text-sm">{cat}</p>
                        </div>
                      </div>
                      <ArrowRight size={14} className="text-slate-400" />
                    </button>
                  ))}
                </>
              )}
            </div>

            {/* Right pane: Related Suggestions from Databricks LLM */}
            {(suggestions?.related_suggestions?.length ?? 0) > 0 && (
              <div className="w-56 border-l border-slate-100 py-2 bg-slate-50/60 flex-shrink-0">
                <div className="px-4 pt-2 pb-1 flex items-center gap-1.5">
                  <Lightbulb size={12} className="text-slate-400" />
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Related Suggestions</p>
                </div>
                {suggestions!.related_suggestions.map((s, i) => (
                  <button
                    key={i}
                    onMouseDown={() => handleSubmit(s)}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-slate-600 hover:bg-primary-50 hover:text-primary-700 transition-colors text-left"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-slate-300 flex-shrink-0" />
                    <span>{s}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading indicator */}
      {loading && open && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-lg border border-slate-100 z-50 p-4 text-center">
          <span className="text-xs text-slate-400 font-medium">Searching Databricks...</span>
        </div>
      )}
    </div>
  )
}

function getCategoryIcon(category: string): string {
  const map: Record<string, string> = {
    'Laptops': '💻',
    'Audio': '🎧',
    'Headphones': '🎧',
    'Smart Watches': '⌚',
    'Office Furniture': '🪑',
    'Office Chairs': '🪑',
    'Home & Kitchen': '☕',
    'Monitors': '🖥️',
    'Audio Devices': '🔊',
    'Electronics': '⚡',
  }
  return map[category] ?? '📦'
}
