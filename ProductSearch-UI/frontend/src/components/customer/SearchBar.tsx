import { useState, useRef, useEffect } from 'react'
import { MagnifyingGlass, X, ArrowRight } from '@phosphor-icons/react'
import { searchAPI } from '@/services/api'
import { clsx } from 'clsx'

const QUICK_SUGGESTIONS = [
  'Gaming laptop under $1500',
  'Ergonomic office chair',
  'Smart watch with health tracking',
  'Espresso coffee machine',
  '4K monitor for design',
  'Noise cancelling headphones',
]

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
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [open, setOpen] = useState(false)
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

  // Fetch suggestions with debounce
  useEffect(() => {
    if (value.length < 2) {
      setSuggestions([])
      return
    }
    const timer = setTimeout(async () => {
      try {
        const s = await searchAPI.getSuggestions(value, 6)
        setSuggestions(s)
      } catch {
        setSuggestions([])
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [value])

  const handleSubmit = (q: string) => {
    if (!q.trim()) return
    setValue(q)
    setOpen(false)
    onSearch(q.trim())
  }

  const highlightMatch = (text: string, query: string) => {
    const idx = text.toLowerCase().indexOf(query.toLowerCase())
    if (idx === -1) return <span>{text}</span>
    return (
      <>
        {text.slice(0, idx)}
        <strong className="font-semibold text-gray-900">{text.slice(idx, idx + query.length)}</strong>
        {text.slice(idx + query.length)}
      </>
    )
  }

  const displaySuggestions = suggestions.length > 0
    ? suggestions
    : value.length === 0 ? QUICK_SUGGESTIONS.slice(0, 5) : []

  return (
    <div ref={containerRef} className="relative w-full">
      <div
        className={clsx(
          'flex items-center gap-2 bg-white border-2 rounded-2xl transition-all duration-200',
          open || value
            ? 'border-primary-400 shadow-lg shadow-primary-100/50'
            : 'border-gray-200 hover:border-gray-300',
          size === 'lg' && 'px-5 py-4',
          size === 'md' && 'px-4 py-3',
          size === 'sm' && 'px-3 py-2',
        )}
      >
        <MagnifyingGlass
          size={size === 'lg' ? 22 : 18}
          weight="bold"
          className="text-gray-400 flex-shrink-0"
        />
        <input
          ref={inputRef}
          value={value}
          onChange={(e) => { setValue(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(value) }}
          placeholder={placeholder}
          className={clsx(
            'flex-1 bg-transparent outline-none text-gray-900 placeholder-gray-400',
            size === 'lg' && 'text-base',
            size === 'md' && 'text-sm',
            size === 'sm' && 'text-sm',
          )}
        />
        {value && (
          <button
            onClick={() => { setValue(''); setSuggestions([]); inputRef.current?.focus() }}
            className="p-1 rounded-full hover:bg-gray-100 transition-colors"
          >
            <X size={16} className="text-gray-400" />
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

      {/* Autocomplete Dropdown */}
      {open && displaySuggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-xl border border-gray-100 z-50 overflow-hidden animate-fade-in">
          <div className="flex">
            {/* Left: Query suggestions */}
            <div className="flex-1 py-2">
              <p className="px-4 pt-2 pb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide">
                {suggestions.length > 0 ? 'Suggestions' : 'Popular Searches'}
              </p>
              {displaySuggestions.map((s, i) => (
                <button
                  key={i}
                  onMouseDown={() => handleSubmit(s)}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-primary-50 hover:text-primary-700 transition-colors text-left"
                >
                  <MagnifyingGlass size={14} className="text-gray-400 flex-shrink-0" />
                  <span>{suggestions.length > 0 ? highlightMatch(s, value) : s}</span>
                </button>
              ))}
            </div>

            {/* Right: Related categories */}
            <div className="w-56 border-l border-gray-100 py-2 bg-gray-50/50">
              <p className="px-4 pt-2 pb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide">
                Categories
              </p>
              {[
                { name: 'Laptops', icon: '💻' },
                { name: 'Audio', icon: '🎧' },
                { name: 'Office Furniture', icon: '🪑' },
                { name: 'Smart Watches', icon: '⌚' },
              ].map((cat) => (
                <button
                  key={cat.name}
                  onMouseDown={() => handleSubmit(cat.name)}
                  className="w-full flex items-center justify-between px-4 py-2.5 text-sm text-gray-700 hover:bg-primary-50 hover:text-primary-700 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <span>{cat.icon}</span>
                    <span>{cat.name}</span>
                  </span>
                  <ArrowRight size={14} className="text-gray-400" />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
