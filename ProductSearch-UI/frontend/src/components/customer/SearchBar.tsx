import { useState, useRef, useEffect } from 'react'
import { MagnifyingGlass, X } from '@phosphor-icons/react'
import { useSearchStore } from '@/store/useSearchStore'
import { searchAPI } from '@/services/api'
import { useDebounce } from '@/hooks/useDebounce'

interface SearchBarProps {
  onSearch?: (query: string) => void
  placeholder?: string
  autoFocus?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function SearchBar({ 
  onSearch, 
  placeholder = "Search for products...",
  autoFocus = false,
  size = 'lg'
}: SearchBarProps) {
  const { query, setQuery } = useSearchStore()
  const [localQuery, setLocalQuery] = useState(query)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)
  
  const debouncedQuery = useDebounce(localQuery, 300)
  
  // Fetch suggestions
  useEffect(() => {
    if (debouncedQuery && debouncedQuery.length >= 2) {
      searchAPI.getSuggestions(debouncedQuery, 5)
        .then(setSuggestions)
        .catch(() => setSuggestions([]))
    } else {
      setSuggestions([])
    }
  }, [debouncedQuery])
  
  // Handle search
  const handleSearch = (searchQuery: string) => {
    if (!searchQuery.trim()) return
    
    setQuery(searchQuery)
    setShowSuggestions(false)
    setSuggestions([])
    onSearch?.(searchQuery)
  }
  
  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (selectedIndex >= 0 && suggestions[selectedIndex]) {
        handleSearch(suggestions[selectedIndex])
      } else {
        handleSearch(localQuery)
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev => 
        prev < suggestions.length - 1 ? prev + 1 : prev
      )
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
      inputRef.current?.blur()
    }
  }
  
  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Size classes
  const sizeClasses = {
    sm: 'h-10 text-sm',
    md: 'h-12 text-base',
    lg: 'h-14 text-lg'
  }
  
  const iconSizes = {
    sm: 18,
    md: 20,
    lg: 24
  }
  
  return (
    <div className="relative w-full">
      <div className="relative">
        {/* Search Icon */}
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
          <MagnifyingGlass size={iconSizes[size]} weight="bold" />
        </div>
        
        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={localQuery}
          onChange={(e) => {
            setLocalQuery(e.target.value)
            setShowSuggestions(true)
            setSelectedIndex(-1)
          }}
          onFocus={() => setShowSuggestions(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className={`
            w-full ${sizeClasses[size]} pl-12 pr-12 
            bg-white border-2 border-gray-200 rounded-2xl
            focus:border-primary-500 focus:ring-4 focus:ring-primary-100
            transition-all duration-200
            placeholder:text-gray-400
            text-gray-900 font-medium
            shadow-sm hover:shadow-md
          `}
          aria-label="Search products"
          aria-autocomplete="list"
          aria-controls="search-suggestions"
          aria-expanded={showSuggestions && suggestions.length > 0}
        />
        
        {/* Clear Button */}
        {localQuery && (
          <button
            onClick={() => {
              setLocalQuery('')
              setQuery('')
              setSuggestions([])
              inputRef.current?.focus()
            }}
            className="
              absolute right-4 top-1/2 -translate-y-1/2
              text-gray-400 hover:text-gray-600
              transition-colors duration-200
              p-1 rounded-lg hover:bg-gray-100
            "
            aria-label="Clear search"
          >
            <X size={iconSizes[size]} weight="bold" />
          </button>
        )}
      </div>
      
      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          id="search-suggestions"
          className="
            absolute top-full left-0 right-0 mt-2
            bg-white border border-gray-200 rounded-xl shadow-lg
            overflow-hidden z-50
            animate-fade-in
          "
          role="listbox"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSearch(suggestion)}
              onMouseEnter={() => setSelectedIndex(index)}
              className={`
                w-full px-4 py-3 text-left
                flex items-center gap-3
                transition-colors duration-150
                ${index === selectedIndex 
                  ? 'bg-primary-50 text-primary-700' 
                  : 'hover:bg-gray-50 text-gray-700'
                }
                ${index !== suggestions.length - 1 ? 'border-b border-gray-100' : ''}
              `}
              role="option"
              aria-selected={index === selectedIndex}
            >
              <MagnifyingGlass 
                size={18} 
                weight={index === selectedIndex ? 'bold' : 'regular'}
                className="flex-shrink-0"
              />
              <span className="font-medium">{suggestion}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
