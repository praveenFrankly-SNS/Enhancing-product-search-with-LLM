import { useState, useEffect } from 'react'
import { FunnelSimple, ArrowCounterClockwise, Star } from '@phosphor-icons/react'
import { SearchFilters } from '@/services/api'

interface FilterSidebarProps {
  filters: SearchFilters
  onFilterChange: (filters: SearchFilters) => void
  categories?: { name: string; count: number }[]
  brands?: { name: string; count: number }[]
  onClear: () => void
}

const DEFAULT_CATEGORIES = [
  { name: 'Office Chairs', count: 243 },
  { name: 'Gaming Chairs', count: 85 },
  { name: 'Dining Chairs', count: 24 },
  { name: 'Stools', count: 18 },
  { name: 'Laptops', count: 1247 },
  { name: 'Smart Watches', count: 423 },
]

const DEFAULT_BRANDS = [
  { name: 'Herman Miller', count: 23 },
  { name: 'Steelcase', count: 31 },
  { name: 'Ergohuman', count: 18 },
  { name: 'SIHOO', count: 27 },
  { name: 'Hbada', count: 16 },
]

export function FilterSidebar({
  filters,
  onFilterChange,
  categories = DEFAULT_CATEGORIES,
  brands = DEFAULT_BRANDS,
  onClear,
}: FilterSidebarProps) {
  const [minPrice, setMinPrice] = useState(filters.min_price || 0)
  const [maxPrice, setMaxPrice] = useState(filters.max_price || 100000)
  const [brandSearch, setBrandSearch] = useState('')

  // Sync state with prop changes
  useEffect(() => {
    setMinPrice(filters.min_price || 0)
    setMaxPrice(filters.max_price || 100000)
  }, [filters.min_price, filters.max_price])

  const handlePriceChange = (min: number, max: number) => {
    onFilterChange({
      ...filters,
      min_price: min,
      max_price: max,
    })
  }

  const toggleCategory = (cat: string) => {
    const isSelected = filters.category === cat
    onFilterChange({
      ...filters,
      category: isSelected ? undefined : cat,
    })
  }

  const toggleBrand = (brand: string) => {
    const isSelected = filters.brand === brand
    onFilterChange({
      ...filters,
      brand: isSelected ? undefined : brand,
    })
  }

  const toggleRating = (rating: number) => {
    const isSelected = filters.min_rating === rating
    onFilterChange({
      ...filters,
      min_rating: isSelected ? undefined : rating,
    })
  }

  const toggleAvailability = () => {
    onFilterChange({
      ...filters,
      in_stock: !filters.in_stock,
    })
  }

  const filteredBrands = brands.filter((b) =>
    b.name.toLowerCase().includes(brandSearch.toLowerCase())
  )

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-6 w-full md:w-64 flex-shrink-0">
      <div className="flex items-center justify-between border-b border-gray-100 pb-4">
        <div className="flex items-center gap-2 font-bold text-gray-900">
          <FunnelSimple size={20} />
          <span>Filters</span>
        </div>
        <button
          onClick={onClear}
          className="text-xs font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1 transition-colors"
        >
          <ArrowCounterClockwise size={14} />
          <span>Clear all</span>
        </button>
      </div>

      {/* Category Filter */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Category</h4>
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
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 w-4 h-4"
                />
                <span className={filters.category === cat.name ? 'font-semibold text-primary-600' : ''}>
                  {cat.name}
                </span>
              </span>
              <span className="text-xs text-gray-400 font-medium">{cat.count}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Price Range Filter */}
      <div className="space-y-3 border-t border-gray-100 pt-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Price Range (₹)</h4>
        <div className="space-y-4">
          <div className="flex gap-2 items-center">
            <input
              type="number"
              value={minPrice}
              onChange={(e) => setMinPrice(Number(e.target.value))}
              onBlur={() => handlePriceChange(minPrice, maxPrice)}
              placeholder="Min"
              className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400"
            />
            <span className="text-gray-400 text-sm">to</span>
            <input
              type="number"
              value={maxPrice}
              onChange={(e) => setMaxPrice(Number(e.target.value))}
              onBlur={() => handlePriceChange(minPrice, maxPrice)}
              placeholder="Max"
              className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400"
            />
          </div>
        </div>
      </div>

      {/* Brand Filter */}
      <div className="space-y-3 border-t border-gray-100 pt-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Brand</h4>
        <input
          type="text"
          placeholder="Search brand..."
          value={brandSearch}
          onChange={(e) => setBrandSearch(e.target.value)}
          className="w-full text-xs border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-400 mb-2"
        />
        <div className="space-y-2 max-h-40 overflow-y-auto">
          {filteredBrands.map((brand) => (
            <label
              key={brand.name}
              className="flex items-center justify-between text-sm text-gray-700 hover:text-gray-900 cursor-pointer"
            >
              <span className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={filters.brand === brand.name}
                  onChange={() => toggleBrand(brand.name)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 w-4 h-4"
                />
                <span className={filters.brand === brand.name ? 'font-semibold text-primary-600' : ''}>
                  {brand.name}
                </span>
              </span>
              <span className="text-xs text-gray-400 font-medium">{brand.count}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Rating Filter */}
      <div className="space-y-3 border-t border-gray-100 pt-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Rating</h4>
        <div className="space-y-2">
          {[4.5, 4.0, 3.5].map((rating) => (
            <button
              key={rating}
              onClick={() => toggleRating(rating)}
              className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 w-full text-left"
            >
              <input
                type="checkbox"
                checked={filters.min_rating === rating}
                readOnly
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 w-4 h-4"
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
            onChange={toggleAvailability}
            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 w-4 h-4"
          />
          <span>In Stock</span>
        </label>
      </div>
    </div>
  )
}
