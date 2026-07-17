import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { CaretLeft, CaretRight, Star } from '@phosphor-icons/react'
import type { RelatedProduct } from '@/services/api'

interface RelatedProductsProps {
  products: RelatedProduct[]
}

export function RelatedProducts({ products }: RelatedProductsProps) {
  const navigate = useNavigate()
  const scrollRef = useRef<HTMLDivElement>(null)
  const [imgErrors, setImgErrors] = useState<Record<string, boolean>>({})

  if (!products || products.length === 0) return null

  const scroll = (dir: 'left' | 'right') => {
    if (!scrollRef.current) return
    scrollRef.current.scrollBy({ left: dir === 'right' ? 320 : -320, behavior: 'smooth' })
  }

  const handleImgError = (id: string) => {
    setImgErrors((prev) => ({ ...prev, [id]: true }))
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-extrabold text-gray-900">
          Related Products You May Like
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => scroll('left')}
            className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center hover:bg-slate-50 transition-all active:scale-95"
            aria-label="Scroll left"
          >
            <CaretLeft size={16} className="text-slate-600" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center hover:bg-slate-50 transition-all active:scale-95"
            aria-label="Scroll right"
          >
            <CaretRight size={16} className="text-slate-600" />
          </button>
          <button className="text-sm font-bold text-blue-600 hover:text-blue-700 ml-2 flex items-center gap-1">
            View all
            <CaretRight size={14} />
          </button>
        </div>
      </div>

      {/* Horizontal scroll strip */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-2 scroll-smooth"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {products.map((rp) => {
          const imageUrl = `http://localhost:8000/api/v1/products/${rp.product_id}/image`
          const hasImg = !imgErrors[rp.product_id]
          const matchPct = rp.similarity_score ? Math.round(rp.similarity_score * 100) : null

          return (
            <div
              key={rp.product_id}
              className="flex-shrink-0 w-64 bg-white border border-slate-200 rounded-2xl overflow-hidden hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer group"
              onClick={() => navigate(`/products/${rp.product_id}`)}
            >
              {/* Image */}
              <div className="relative aspect-[4/3] bg-slate-100 overflow-hidden">
                <img
                  src={imageUrl}
                  alt={rp.product_name || 'Product'}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  onError={() => handleImgError(rp.product_id)}
                />
                {!hasImg && (
                  <div className="absolute inset-0 flex items-center justify-center bg-slate-100 text-3xl">
                    📦
                  </div>
                )}
                {matchPct !== null && (
                  <div className="absolute top-2 right-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                    {matchPct}% Match
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="p-4 space-y-2">
                <p className="text-xs text-blue-600 font-semibold uppercase tracking-wide truncate">
                  {rp.category_path || ''}
                </p>
                <h4 className="text-sm font-bold text-slate-900 line-clamp-2 group-hover:text-blue-600 transition-colors leading-snug">
                  {rp.product_name || 'Product'}
                </h4>
                {rp.brand_name && (
                  <p className="text-xs text-slate-500">{rp.brand_name}</p>
                )}

                {/* Stars */}
                {rp.average_rating && (
                  <div className="flex items-center gap-1.5">
                    <div className="flex items-center gap-0.5">
                      {[1, 2, 3, 4, 5].map((s) => (
                        <Star
                          key={s}
                          size={12}
                          weight={rp.average_rating! >= s ? 'fill' : 'regular'}
                          className={rp.average_rating! >= s ? 'text-amber-400' : 'text-gray-300'}
                        />
                      ))}
                    </div>
                    <span className="text-xs text-gray-500 font-medium">
                      {rp.average_rating.toFixed(1)} ({rp.review_count})
                    </span>
                  </div>
                )}

                {/* Price + stock */}
                <div className="flex items-center justify-between pt-1">
                  <span className="font-bold text-sm text-slate-900">
                    {rp.selling_price
                      ? `₹${rp.selling_price.toLocaleString('en-IN')}`
                      : 'On request'}
                  </span>
                  <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full">
                    In Stock
                  </span>
                </div>

                <button className="w-full py-1.5 text-xs font-semibold text-blue-600 border border-blue-200 rounded-xl hover:bg-blue-600 hover:text-white transition-all duration-200">
                  View Details
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
