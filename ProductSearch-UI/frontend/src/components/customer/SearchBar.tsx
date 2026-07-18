import { useState, useRef, useEffect } from 'react'
import { MagnifyingGlass, X } from '@phosphor-icons/react'
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
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus()
  }, [autoFocus])

  const handleSubmit = (q: string) => {
    if (!q.trim()) return
    setValue(q)
    onSearch(q.trim())
  }

  return (
    <div className="relative w-full">
      <div
        className={clsx(
          'flex items-center gap-2 bg-white border-2 rounded-2xl transition-all duration-200',
          value
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
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit(value)
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
            onClick={() => { setValue(''); inputRef.current?.focus() }}
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
    </div>
  )
}
