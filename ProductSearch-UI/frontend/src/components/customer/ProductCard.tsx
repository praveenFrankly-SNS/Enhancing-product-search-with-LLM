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

export function ProductCard({ product, showScore = false, isBestMatch = false }: ProductCardProps) {
  const navigate = useNavigate()
  const [wishlisted, setWishlisted] = useState(false)
  const matchPct = product.similarity_score
    ? Math.round(product.similarity_score * 100)
    : null

  const handleClick = () => navigate(`/products/${product.product_id}`)

  const hasImage = false;

  return (
    <div
      className="group bg-white rounded-2xl overflow-hidden border border-gray-100 hover:border-primary-200 hover:shadow-soft transition-all duration-300 cursor-pointer flex flex-col justify-between"
      onClick={handleClick}
    >
      {/* Image Container (Only if image is present) */}
      {hasImage ? (
        <div className="relative aspect-square bg-gray-50 overflow-hidden">
          <img
            src={product.image_url || ''}
            alt={product.product_name || 'Product'}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />

          {/* Best Match badge */}
          {isBestMatch && (
            <div className="absolute top-3 left-3 bg-emerald-500 text-white text-xs font-bold px-2.5 py-1 rounded-full">
              Best Match
            </div>
          )}

          {/* Similarity score badge */}
          {showScore && matchPct !== null && (
            <div className={clsx(
              'absolute top-3 right-3 text-xs font-bold px-2.5 py-1 rounded-full',
              matchPct >= 90 ? 'bg-emerald-100 text-emerald-700' :
              matchPct >= 75 ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-600'
            )}>
              {matchPct}% Match
            </div>
          )}

          {/* Wishlist */}
          <button
            className="absolute bottom-3 right-3 w-8 h-8 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm hover:bg-white transition-all duration-200 opacity-0 group-hover:opacity-100"
            onClick={(e) => { e.stopPropagation(); setWishlisted(!wishlisted) }}
            aria-label="Add to wishlist"
          >
            <Heart
              size={16}
              weight={wishlisted ? 'fill' : 'regular'}
              className={wishlisted ? 'text-red-500' : 'text-gray-500'}
            />
          </button>
        </div>
      ) : (
        /* Inline metadata when image is absent */
        <div className="px-4 pt-4 flex items-center justify-between gap-2">
          {isBestMatch ? (
            <span className="bg-emerald-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
              Best Match
            </span>
          ) : <span />}
          
          {showScore && matchPct !== null && (
            <span className={clsx(
              'text-[10px] font-bold px-2 py-0.5 rounded-full',
              matchPct >= 90 ? 'bg-emerald-100 text-emerald-700' :
              matchPct >= 75 ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-600'
            )}>
              {matchPct}% Match
            </span>
          )}
        </div>
      )}

      {/* Content */}
      <div className="p-4 space-y-2 flex-1 flex flex-col justify-between">
        <div className="space-y-2">
          {product.category && (
            <p className="text-xs text-primary-600 font-medium uppercase tracking-wide truncate">
              {product.category}
            </p>
          )}

          <h3 className="font-semibold text-gray-900 text-sm leading-snug line-clamp-3 group-hover:text-primary-700 transition-colors">
            {product.product_name || 'Unnamed Product'}
          </h3>

          {product.brand && (
            <p className="text-xs text-gray-500">{product.brand}</p>
          )}

          <StarRating rating={product.avg_rating} count={product.review_count} />
        </div>

        <div className="space-y-3 pt-2">
          {/* Price + stock row */}
          <div className="flex items-center justify-between pt-1">
            <div>
              {product.price ? (
                <span className="text-base font-bold text-gray-900">
                  ₹{product.price.toLocaleString('en-IN')}
                </span>
              ) : (
                <span className="text-sm text-gray-400">Price on request</span>
              )}
            </div>
            <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
              In Stock
            </span>
          </div>

          {/* View Details */}
          <button
            className="w-full py-2 text-sm font-semibold text-primary-600 border border-primary-200 rounded-xl hover:bg-primary-600 hover:text-white hover:border-primary-600 transition-all duration-200"
            onClick={handleClick}
          >
            View Details
          </button>
        </div>
      </div>
    </div>
  )
}
