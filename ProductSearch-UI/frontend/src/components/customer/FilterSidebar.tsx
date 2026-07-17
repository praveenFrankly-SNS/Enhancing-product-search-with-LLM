import { useState, useEffect } from 'react'
import { FunnelSimple, ArrowCounterClockwise, Star, SpinnerGap } from '@phosphor-icons/react'
import { useQuery } from '@tanstack/react-query'
import { searchAPI, SearchFilters } from '@/services/api'

interface FilterSidebarProps {
  filters: SearchFilters
  onFilterChange: (filters: SearchFilters) => void
  onClear: () => void
}

export function FilterSidebar({
  filters,
  onFilterChange,
  onClear,
}: FilterSidebarProps) {
  const [minPrice, setMinPrice] = useState(filters.min_price ?? 0)
  const [maxPrice, setMaxPrice] = useState(filters.max_price ?? 200000)
  const [brandSearch, setBrandSearch] = useState('')
  const [showAllBrands, setShowAllBrands] = useState(false)

  // Sync state with filter prop changes
  useEffect(() => {
    setMinPrice(filters.min_price ?? 0)
    setMaxPrice(filters.max_price ?? 200000)
  }, [filters.min_price, filters.max_price])

  // Fetch categories from Databricks Gold table
  const { data: categories = [], isLoading: catsLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: searchAPI.getCategories,
    staleTime: 5 * 60 * 1000,
  })

  // Fetch brands, filtered by selected category
  const { data: brands = [], isLoading: brandsLoading } = useQuery({
    queryKey: ['brands', filters.category],
    queryFn: () => searchAPI.getBrands(filters.category),
    staleTime: 5 * 60 * 1000,
  })

  const handlePriceChange = (min: number, max: number) => {
    onFilterChange({ ...filters, min_price: min, max_price: max })
  }

  const toggleCategory = (cat: string) => {
    const isSelected = filters.category === cat
    onFilterChange({ ...filters, category: isSelected ? undefined : cat })
  }

  const toggleBrand = (brand: string) => {
    const isSelected = filters.brand === brand
    onFilterChange({ ...filters, brand: isSelected ? undefined : brand })
  }

  const toggleRating = (rating: number) => {
    const isSelected = filters.min_rating === rating
    onFilterChange({ ...filters, min_rating: isSelected ? undefined : rating })
  }

  const filteredBrands = brands.filter((b) =>
    b.name.toLowerCase().includes(brandSearch.toLowerCase())
  )
  const displayBrands = showAllBrands ? filteredBrands : filteredBrands.slice(0, 5)

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-6 w-full md:w-64 flex-shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 pb-4">
        <div className="flex items-center gap-2 font-bold text-gray-900">
          <FunnelSimple size={20} />
          <span>Filters</span>
        </div>
        <button
          onClick={onClear}
          className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 transition-colors"
        >
          <ArrowCounterClockwise size={14} />
          <span>Clear all</span>
        </button>
      </div>

      {/* Category Filter — from Databricks */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Category</h4>
        {catsLoading ? (
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <SpinnerGap size={14} className="animate-spin" />
            <span>Loading...</span>
          </div>
        ) : (
          <div className="space-y-2">
            {categories.map((cat) => (
              <label
                key={cat.name}
                className="flex items-center justify-between text-sm text-gray-700 hover:text-gray-900 cursor-pointer"
              >
                <span className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={filters.category === cat.name}
                    onChange={() => toggleCategory(cat.name)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                  />
                  <span className={filters.category === cat.name ? 'font-semibold text-blue-600' : ''}>
                    {cat.name}
                  </span>
                </span>
                <span className="text-xs text-gray-400 font-medium">{cat.count.toLocaleString()}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Price Range Filter */}
      <div className="space-y-3 border-t border-gray-100 pt-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Price Range (₹)</h4>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            value={minPrice}
            onChange={(e) => setMinPrice(Number(e.target.value))}
            onBlur={() => handlePriceChange(minPrice, maxPrice)}
            placeholder="Min"
            className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-blue-400"
          />
          <span className="text-gray-400 text-sm">to</span>
          <input
            type="number"
            value={maxPrice}
            onChange={(e) => setMaxPrice(Number(e.target.value))}
            onBlur={() => handlePriceChange(minPrice, maxPrice)}
            placeholder="Max"
            className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-blue-400"
          />
        </div>
      </div>

      {/* Brand Filter — from Databricks */}
      <div className="space-y-3 border-t border-gray-100 pt-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Brand</h4>
        <input
          type="text"
          placeholder="Search brand..."
          value={brandSearch}
          onChange={(e) => setBrandSearch(e.target.value)}
          className="w-full text-xs border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-blue-400 mb-2"
        />
        {brandsLoading ? (
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <SpinnerGap size={14} className="animate-spin" />
            <span>Loading brands...</span>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {displayBrands.map((brand) => (
                <label
                  key={brand.name}
                  className="flex items-center justify-between text-sm text-gray-700 hover:text-gray-900 cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={filters.brand === brand.name}
                      onChange={() => toggleBrand(brand.name)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                    />
                    <span className={filters.brand === brand.name ? 'font-semibold text-blue-600' : ''}>
                      {brand.name}
                    </span>
                  </span>
                  <span className="text-xs text-gray-400 font-medium">{brand.count}</span>
                </label>
              ))}
            </div>
            {filteredBrands.length > 5 && (
              <button
                onClick={() => setShowAllBrands(!showAllBrands)}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 mt-1"
              >
                {showAllBrands ? 'Show less' : `Show more (${filteredBrands.length - 5} more)`}
              </button>
            )}
          </>
        )}
      </div>

      {/* Rating Filter */}
      <div className="space-y-3 border-t border-gray-100 pt-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Rating</h4>
        <div className="space-y-2">
          {[5, 4, 3].map((rating) => (
            <button
              key={rating}
              onClick={() => toggleRating(rating)}
              className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 w-full text-left"
            >
              <input
                type="checkbox"
                checked={filters.min_rating === rating}
                readOnly
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
              />
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star
                    key={s}
                    size={14}
                    weight={rating >= s ? 'fill' : 'regular'}
                    className={rating >= s ? 'text-amber-400' : 'text-gray-300'}
                  />
                ))}
              </div>
              <span className="text-xs text-gray-500">& up</span>
              <span className="ml-auto text-xs text-gray-400">
                {/* count displayed from results */}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Availability Filter */}
      <div className="space-y-3 border-t border-gray-100 pt-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Availability</h4>
        <label className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 cursor-pointer">
          <input
            type="checkbox"
            checked={!!filters.in_stock}
            onChange={() => onFilterChange({ ...filters, in_stock: !filters.in_stock })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
          />
          <span>In Stock</span>
        </label>
      </div>
    </div>
  )
}
