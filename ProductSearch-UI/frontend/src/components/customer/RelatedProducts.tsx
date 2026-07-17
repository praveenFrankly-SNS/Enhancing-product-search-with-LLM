import { ProductCard } from './ProductCard'
import type { RelatedProduct } from '@/services/api'

interface RelatedProductsProps {
  products: RelatedProduct[]
}

export function RelatedProducts({ products }: RelatedProductsProps) {
  if (!products || products.length === 0) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-gray-900 font-display">
          Related Products You May Like
        </h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {products.map((rp) => {
          // Map RelatedProduct fields to Product Card compatible format
          const mappedProduct = {
            product_id: rp.product_id,
            product_name: rp.product_name || 'Unnamed Product',
            description: null,
            brand: rp.brand_name,
            category: rp.category_path,
            price: rp.selling_price,
            currency: 'INR',
            attributes: null,
            avg_rating: rp.average_rating,
            review_count: rp.review_count,
            similarity_score: rp.similarity_score,
            image_url: null,
          }

          return (
            <ProductCard
              key={rp.product_id}
              product={mappedProduct}
              showScore={true}
            />
          )
        })}
      </div>
    </div>
  )
}
