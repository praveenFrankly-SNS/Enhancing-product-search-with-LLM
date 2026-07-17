import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { searchAPI } from '@/services/api'
import { RelatedProducts } from '@/components/customer/RelatedProducts'
import {
  ArrowLeft,
  ShareNetwork,
  Star,
  CheckCircle,
  ShieldCheck,
  SpinnerGap,
  Sparkle,
  Truck,
  ArrowCounterClockwise,
  SealCheck
} from '@phosphor-icons/react'

const KEY_FEATURES = [
  'Fully customizable ergonomic alignment controls',
  'Advanced temperature regulation & breathability',
  'Flexible adjustments (armrests, seat depth, lumbar support)',
  'Premium material build designed for durability',
  'Standard product catalog specifications compliance',
  'Comprehensive manufacturer warranty coverage included'
]

export function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [selectedSize, setSelectedSize] = useState('B')
  const [selectedFrame, setSelectedFrame] = useState('graphite')
  const [selectedCasters, setSelectedCasters] = useState('carpet')
  const [activeImgIdx, setActiveImgIdx] = useState(0)

  // Fetch product detail (includes related_products automatically)
  const { data: product, isLoading, isError } = useQuery({
    queryKey: ['product', id],
    queryFn: () => searchAPI.getProduct(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <SpinnerGap size={40} className="text-primary-600 animate-spin" />
          <p className="text-sm font-bold text-slate-500">Fetching Product Details...</p>
        </div>
      </div>
    )
  }

  if (isError || !product) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center p-8 bg-white border border-slate-200 rounded-3xl max-w-sm">
          <span className="text-4xl">⚠️</span>
          <h3 className="text-lg font-bold text-slate-800 mt-4 mb-2">Product Not Found</h3>
          <p className="text-sm text-slate-500 mb-6">This item is not present in the catalog index.</p>
          <button
            onClick={() => navigate('/search')}
            className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-bold rounded-xl text-sm"
          >
            Back to Search
          </button>
        </div>
      </div>
    )
  }

  // Gallery images mock using seeded index
  const seedBase = absHash(product.product_id)
  const galleryImages = [
    `https://picsum.photos/seed/${seedBase}/600/600`,
    `https://picsum.photos/seed/${seedBase + 1}/600/600`,
    `https://picsum.photos/seed/${seedBase + 2}/600/600`,
    `https://picsum.photos/seed/${seedBase + 3}/600/600`,
  ]

  // Parse custom features if available from gold table schema attributes/attribute_summary
  const descriptionText = product.description || 'No detailed description available.'

  const hasImage = !!product.image_url && product.image_url !== '';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Header navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="p-2 rounded-xl hover:bg-slate-100 transition-all active:scale-95 text-slate-700 flex items-center gap-1.5"
            >
              <ArrowLeft size={18} weight="bold" />
              <span className="text-sm font-bold hidden sm:inline">Back</span>
            </button>
            <span className="text-slate-300">/</span>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider truncate max-w-[200px]">
              {product.category || 'Product Details'}
            </span>
          </div>

          <button className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 transition-all active:scale-95 text-slate-700 flex items-center gap-1.5 text-xs font-bold">
            <ShareNetwork size={16} />
            <span>Share</span>
          </button>
        </div>
      </header>

      {/* Main product card layout */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-8 w-full space-y-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-sm">
          {/* Left image column */}
          {hasImage && (
            <div className="lg:col-span-6 space-y-4">
              <div className="relative aspect-square bg-slate-50 border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
                <img
                  src={galleryImages[activeImgIdx]}
                  alt={product.product_name}
                  className="w-full h-full object-cover transition-all duration-300"
                />
                <span className="absolute top-4 left-4 bg-primary-600 text-white text-xs font-extrabold px-3 py-1 rounded-full flex items-center gap-1">
                  <Sparkle size={12} weight="fill" />
                  <span>94% Match</span>
                </span>
              </div>

              {/* Thumbnail previews */}
              <div className="grid grid-cols-4 gap-4">
                {galleryImages.map((img, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveImgIdx(i)}
                    className={`
                      aspect-square rounded-xl overflow-hidden border-2 bg-slate-50 transition-all
                      ${activeImgIdx === i ? 'border-primary-500 scale-95 shadow-sm' : 'border-transparent hover:border-slate-200'}
                    `}
                  >
                    <img src={img} alt="Thumbnail preview" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Right details column */}
          <div className={hasImage ? "lg:col-span-6 flex flex-col justify-between space-y-6" : "lg:col-span-12 flex flex-col justify-between space-y-6"}>
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-bold text-primary-600 uppercase tracking-widest">
                    {product.brand || 'Premium Brand'}
                  </p>
                  <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 mt-1 leading-tight font-display">
                    {product.product_name}
                  </h2>
                </div>
                {!hasImage && (
                  <span className="bg-primary-600 text-white text-xs font-extrabold px-3 py-1.5 rounded-full flex items-center gap-1">
                    <Sparkle size={12} weight="fill" />
                    <span>94% Match</span>
                  </span>
                )}
              </div>

              {/* Star ratings */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-0.5">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Star
                      key={s}
                      size={16}
                      weight={product.avg_rating && product.avg_rating >= s ? 'fill' : 'regular'}
                      className={product.avg_rating && product.avg_rating >= s ? 'text-amber-400' : 'text-slate-200'}
                    />
                  ))}
                </div>
                <span className="text-xs font-bold text-slate-600">
                  {product.avg_rating?.toFixed(1) || '4.5'} ({product.review_count.toLocaleString()} customer reviews)
                </span>
              </div>

              {/* Price row */}
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-black text-slate-900">
                  ₹{product.price?.toLocaleString('en-IN') || '1,10,000'}
                </span>
                <span className="text-sm font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 rounded-full px-2.5 py-0.5">
                  In Stock
                </span>
              </div>

              {/* Descriptions & key benefits */}
              <div className="space-y-2">
                <p className="text-sm text-slate-500 leading-relaxed">
                  {descriptionText}
                </p>
                {product.attribute_summary && (
                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 text-xs font-semibold text-slate-600 leading-relaxed">
                    <span className="text-primary-700 block mb-1">AI Generated Summary:</span>
                    {product.attribute_summary}
                  </div>
                )}
              </div>

              {/* Key Features checklists */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
                {KEY_FEATURES.map((feat, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs font-semibold text-slate-600">
                    <CheckCircle size={16} weight="fill" className="text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Options Panel configuration */}
            <div className="border-t border-slate-200 pt-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Size selections */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Select Size</span>
                  <div className="flex gap-2">
                    {['A', 'B', 'C'].map((size) => (
                      <button
                        key={size}
                        onClick={() => setSelectedSize(size)}
                        className={`
                          px-4 py-2 text-xs font-bold rounded-xl border transition-all active:scale-95
                          ${selectedSize === size
                            ? 'bg-primary-600 border-primary-600 text-white shadow-sm'
                            : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                          }
                        `}
                      >
                        Size {size}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Frame configuration */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Frame / Base</span>
                  <select
                    value={selectedFrame}
                    onChange={(e) => setSelectedFrame(e.target.value)}
                    className="w-full text-xs font-bold bg-white border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-primary-400"
                  >
                    <option value="graphite">Graphite Frame / Base</option>
                    <option value="polished">Polished Aluminum</option>
                    <option value="mineral">Mineral Frame / Base</option>
                  </select>
                </div>
              </div>

              {/* Casters configuration */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Casters</span>
                <select
                  value={selectedCasters}
                  onChange={(e) => setSelectedCasters(e.target.value)}
                  className="w-full text-xs font-bold bg-white border border-slate-200 rounded-xl px-3 py-2.5 outline-none focus:border-primary-400"
                >
                  <option value="carpet">Standard 2.5-inch Carpet Casters</option>
                  <option value="hardfloor">Hard Floor Casters with Quiet Roll</option>
                </select>
              </div>

              {/* CTAs */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <button className="flex-1 bg-primary-600 hover:bg-primary-700 text-white text-sm font-bold py-3 rounded-xl transition-all active:scale-95 shadow-md shadow-primary-200">
                  Add to Cart
                </button>
                <button className="flex-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 text-sm font-bold py-3 rounded-xl transition-all active:scale-95">
                  Buy Now
                </button>
              </div>

              {/* Secure checkout info */}
              <div className="bg-emerald-50/50 border border-emerald-100 rounded-2xl p-4 flex gap-3 text-xs font-medium text-slate-600">
                <ShieldCheck size={20} className="text-emerald-600 flex-shrink-0" weight="fill" />
                <div>
                  <p className="font-bold text-slate-800">Secure & Trusted Merchant</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Encrypted payment gateways, 30-day return policy, and authentic warranty coverage.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Related items section */}
        {product.related_products && product.related_products.length > 0 && (
          <div className="border-t border-slate-200 pt-12">
            <RelatedProducts products={product.related_products} />
          </div>
        )}

        {/* Value Proposition Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 bg-white border border-slate-200 rounded-3xl p-6 shadow-sm text-center">
          <div className="space-y-2 flex flex-col items-center">
            <div className="w-12 h-12 rounded-full bg-primary-50 flex items-center justify-center text-primary-600">
              <Truck size={24} weight="fill" />
            </div>
            <h4 className="font-bold text-sm text-slate-900">Free Express Delivery</h4>
            <p className="text-xs text-slate-500 max-w-[200px]">On all orders above ₹50,000</p>
          </div>
          <div className="space-y-2 flex flex-col items-center border-y sm:border-y-0 sm:border-x border-slate-100 py-6 sm:py-0">
            <div className="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center text-purple-600">
              <ArrowCounterClockwise size={24} weight="fill" />
            </div>
            <h4 className="font-bold text-sm text-slate-900">30-Day Hassle-Free Returns</h4>
            <p className="text-xs text-slate-500 max-w-[200px]">No questions asked fallback policy</p>
          </div>
          <div className="space-y-2 flex flex-col items-center">
            <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
              <SealCheck size={24} weight="fill" />
            </div>
            <h4 className="font-bold text-sm text-slate-900">Genuine Product Guarantee</h4>
            <p className="text-xs text-slate-500 max-w-[200px]">100% authentic vendor verification</p>
          </div>
        </div>
      </main>
    </div>
  )
}

function absHash(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash)
}
