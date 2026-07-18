import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Heart, Star } from '@phosphor-icons/react'
import type { Product } from '@/services/api'
import { clsx } from 'clsx'

interface ProductCardProps {
  product: Product
  showScore?: boolean
  isBestMatch?: boolean
}

function StarRating({ rating, count }: { rating: number | null; count: number }) {
  if (!rating) return null
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((s) => (
          <Star
            key={s}
            size={13}
            weight={rating >= s ? 'fill' : 'regular'}
            className={rating >= s ? 'text-amber-400' : 'text-gray-300'}
          />
        ))}
      </div>
      <span className="text-xs text-gray-500 font-medium">
        {rating.toFixed(1)} ({count.toLocaleString()})
      </span>
    </div>
  )
}

function formatLeafCategory(rawPath?: string | null): string {
  if (!rawPath) return ''
  const parts = rawPath.split(/\s*(?:>|›|\/)\s*/).filter(Boolean)
  return parts.length > 0 ? parts[parts.length - 1] : rawPath
}

export function ProductCard({ product, showScore = false, isBestMatch = false }: ProductCardProps) {
  const navigate = useNavigate()
  const [wishlisted, setWishlisted] = useState(false)
  const [imgError, setImgError] = useState(false)

  const matchPct = product.similarity_score
    ? Math.round(product.similarity_score * 100)
    : null

  const handleClick = () => navigate(`/products/${product.product_id}`, {
    state: { similarity_score: product.similarity_score }
  })
  const displayCategory = formatLeafCategory(product.category)
  const displayTitle = product.product_name && product.product_name !== 'Unnamed Product'
    ? product.product_name
    : `Product ${product.product_id}`

  return (
    <div
      className="group bg-white rounded-2xl overflow-hidden border border-slate-200/80 hover:border-blue-300 hover:shadow-xl transition-all duration-300 cursor-pointer flex flex-col justify-between"
      onClick={handleClick}
    >
      {/* Top Image Frame */}
      <div className="relative aspect-[4/3] bg-slate-50 border-b border-slate-100 overflow-hidden flex flex-col items-center justify-center p-2 text-center">
        {product.image_url && !imgError ? (
          <img
            src={product.image_url}
            alt={displayTitle}
            className="w-full h-full object-contain p-2 group-hover:scale-105 transition-transform duration-300"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-6">
            <div className="w-12 h-12 rounded-2xl bg-white shadow-sm border border-slate-200/60 flex items-center justify-center text-slate-400 mb-1">
              <svg className="w-6 h-6 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">No Image</span>
          </div>
        )}

        {/* Floating Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          {isBestMatch ? (
            <span className="bg-emerald-500 text-white text-[11px] font-extrabold px-2.5 py-1 rounded-full shadow-sm">
              Best Match
            </span>
          ) : <span />}

          {showScore && matchPct !== null && (
            <span className={clsx(
              'text-[11px] font-extrabold px-2.5 py-1 rounded-full shadow-sm backdrop-blur-md',
              matchPct >= 90 ? 'bg-emerald-600 text-white' :
              matchPct >= 75 ? 'bg-blue-600 text-white' :
              'bg-slate-700 text-white'
            )}>
              {matchPct}% Match
            </span>
          )}
        </div>

        {/* Wishlist heart button */}
        <button
          className="absolute bottom-3 right-3 w-8 h-8 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm hover:bg-white transition-all duration-200 opacity-0 group-hover:opacity-100"
          onClick={(e) => { e.stopPropagation(); setWishlisted(!wishlisted) }}
          aria-label="Add to wishlist"
        >
          <Heart
            size={16}
            weight={wishlisted ? 'fill' : 'regular'}
            className={wishlisted ? 'text-red-500' : 'text-slate-500'}
          />
        </button>
      </div>

      {/* Content Body */}
      <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
        <div className="space-y-1.5">
          {displayCategory && (
            <p className="text-[11px] text-blue-600 font-bold uppercase tracking-wider truncate">
              {displayCategory}
            </p>
          )}

          <h3 className="font-bold text-slate-900 text-sm leading-snug line-clamp-2 group-hover:text-blue-600 transition-colors">
            {displayTitle}
          </h3>

          {product.brand && (
            <p className="text-xs text-slate-500 font-medium">{product.brand}</p>
          )}

          <StarRating rating={product.avg_rating} count={product.review_count} />
        </div>

        <div className="space-y-3 pt-1">
          {/* Price + stock */}
          <div className="flex items-center justify-between">
            <div>
              {product.price && product.price > 0 ? (
                <span className="text-base font-extrabold text-slate-900">
                  ₹{product.price.toLocaleString('en-IN')}
                </span>
              ) : (
                <span className="text-xs font-semibold text-slate-400">Price on request</span>
              )}
            </div>
            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2 py-0.5 rounded-full">
              In Stock
            </span>
          </div>

          {/* View Details button */}
          <button
            className="w-full py-2 text-xs font-bold text-blue-600 border border-blue-200/80 rounded-xl hover:bg-blue-600 hover:text-white hover:border-blue-600 transition-all duration-200"
            onClick={handleClick}
          >
            View Details
          </button>
        </div>
      </div>
    </div>
  )
}
