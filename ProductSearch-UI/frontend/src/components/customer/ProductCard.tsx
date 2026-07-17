import { Star, Package } from '@phosphor-icons/react'
import { Product } from '@/services/api'
import { useNavigate } from 'react-router-dom'

interface ProductCardProps {
  product: Product
  showScore?: boolean
}

export function ProductCard({ product, showScore = false }: ProductCardProps) {
  const navigate = useNavigate()
  
  const formatPrice = (price: number | null, currency: string) => {
    if (price === null) return 'Price unavailable'
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: 0,
    }).format(price)
  }
  
  const handleClick = () => {
    navigate(`/product/${product.product_id}`)
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }
  
  return (
    <div
      onClick={handleClick}
      onKeyPress={handleKeyPress}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${product.product_name}`}
      className="
        group relative
        bg-white rounded-2xl overflow-hidden
        border border-gray-200 hover:border-primary-300
        shadow-card hover:shadow-soft
        transition-all duration-300
        cursor-pointer
        focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
      "
    >
      {/* Similarity Score Badge */}
      {showScore && product.similarity_score !== null && (
        <div className="absolute top-3 right-3 z-10">
          <div className="
            bg-primary-500 text-white text-xs font-bold
            px-2.5 py-1 rounded-full
            shadow-md
          ">
            {Math.round(product.similarity_score * 100)}% match
          </div>
        </div>
      )}
      
      {/* Product Image */}
      <div className="
        aspect-square bg-gradient-to-br from-gray-100 to-gray-200
        flex items-center justify-center
        overflow-hidden
        group-hover:scale-105 transition-transform duration-300
      ">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.product_name}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <Package size={64} weight="thin" className="text-gray-400" />
        )}
      </div>
      
      {/* Product Info */}
      <div className="p-4 space-y-2">
        {/* Brand & Category */}
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {product.brand && (
            <>
              <span className="font-medium">{product.brand}</span>
              {product.category && <span>•</span>}
            </>
          )}
          {product.category && <span>{product.category}</span>}
        </div>
        
        {/* Product Name */}
        <h3 className="
          text-base font-semibold text-gray-900
          line-clamp-2 min-h-[3rem]
          group-hover:text-primary-600 transition-colors
        ">
          {product.product_name}
        </h3>
        
        {/* Description */}
        {product.description && (
          <p className="text-sm text-gray-600 line-clamp-2 min-h-[2.5rem]">
            {product.description}
          </p>
        )}
        
        {/* Rating & Reviews */}
        {product.avg_rating !== null && (
          <div className="flex items-center gap-2 pt-1">
            <div className="flex items-center gap-1">
              <Star size={16} weight="fill" className="text-yellow-400" />
              <span className="text-sm font-semibold text-gray-900">
                {product.avg_rating.toFixed(1)}
              </span>
            </div>
            {product.review_count > 0 && (
              <span className="text-xs text-gray-500">
                ({product.review_count.toLocaleString()} reviews)
              </span>
            )}
          </div>
        )}
        
        {/* Price */}
        <div className="pt-2 border-t border-gray-100">
          <div className="text-2xl font-bold text-primary-600">
            {formatPrice(product.price, product.currency)}
          </div>
        </div>
      </div>
      
      {/* Hover Overlay */}
      <div className="
        absolute inset-0 
        bg-gradient-to-t from-primary-600/5 to-transparent
        opacity-0 group-hover:opacity-100
        transition-opacity duration-300
        pointer-events-none
      " />
    </div>
  )
}
