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
  SealCheck,
  House,
  CaretRight,
  Heart,
} from '@phosphor-icons/react'
import { ShoppingCart, Globe, User } from 'lucide-react'

// Parse key features from attribute_summary text
function parseFeatures(text: string | null | undefined): string[] {
  if (!text) return []
  // Split on common delimiters: comma, semicolon, period after a phrase
  const parts = text
    .split(/[,;]/)
    .map((s) => s.trim())
    .filter((s) => s.length > 5 && s.length < 120)
  return parts.slice(0, 6)
}

export function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [selectedSize, setSelectedSize] = useState('B')
  const [selectedFrame, setSelectedFrame] = useState('graphite')
  const [selectedCasters, setSelectedCasters] = useState('carpet')
  const [activeImgIdx, setActiveImgIdx] = useState(0)
  const [wishlisted, setWishlisted] = useState(false)
  const [imgErrors, setImgErrors] = useState<Record<number, boolean>>({})

  const { data: product, isLoading, isError } = useQuery({
    queryKey: ['product', id],
    queryFn: () => searchAPI.getProduct(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <SpinnerGap size={40} className="text-blue-600 animate-spin" />
          <p className="text-sm font-bold text-slate-500">Fetching Product Details...</p>
        </div>
      </div>
    )
  }

  if (isError || !product) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center p-8 bg-white border border-slate-200 rounded-3xl max-w-sm shadow-sm">
          <span className="text-4xl">⚠️</span>
          <h3 className="text-lg font-bold text-slate-800 mt-4 mb-2">Product Not Found</h3>
          <p className="text-sm text-slate-500 mb-6">This item is not in the catalog index.</p>
          <button
            onClick={() => navigate('/search')}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm"
          >
            Back to Search
          </button>
        </div>
      </div>
    )
  }

  // Gallery images using product ID as seed
  const seed = absHash(product.product_id)
  const galleryImages = [
    `https://picsum.photos/seed/${seed}/600/600`,
    `https://picsum.photos/seed/${seed + 1}/600/600`,
    `https://picsum.photos/seed/${seed + 2}/600/600`,
    `https://picsum.photos/seed/${seed + 3}/600/600`,
    `https://picsum.photos/seed/${seed + 4}/600/600`,
  ]

  const matchPct = product.similarity_score ? Math.round(product.similarity_score * 100) : 94

  // Parse real features from attribute_summary from Databricks
  const keyFeatures = parseFeatures(product.attribute_summary)

  const descriptionText = product.description || product.attribute_summary || 'No description available.'

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" className="text-white">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-extrabold text-slate-900 leading-none">ProductSearch</p>
              <p className="text-[9px] text-slate-400 font-semibold">Databricks Accelerator</p>
            </div>
          </div>

          <nav className="hidden lg:flex items-center gap-6 text-sm font-semibold text-slate-500">
            <a href="/" className="hover:text-slate-900">Home</a>
            <a href="#about" className="hover:text-slate-900">About</a>
            <a href="#how-it-works" className="hover:text-slate-900">How it Works</a>
            <a href="#help" className="hover:text-slate-900">Help</a>
          </nav>

          <div className="flex items-center gap-3 text-slate-500">
            <button className="hidden md:flex items-center gap-1.5 text-sm font-semibold hover:text-slate-900 transition-colors">
              <Globe size={16} />
              <span>English</span>
            </button>
            <button className="hidden md:flex items-center gap-1.5 text-sm font-semibold hover:text-slate-900 transition-colors">
              <User size={16} />
              <span>Guest</span>
            </button>
            <button className="relative hover:text-slate-900 transition-colors">
              <ShoppingCart size={20} />
              <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-blue-600 text-white text-[9px] font-bold rounded-full flex items-center justify-center">2</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── Breadcrumb + Back ────────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-6 py-4 w-full flex items-center justify-between">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-slate-500">
          <button onClick={() => navigate('/')} className="hover:text-slate-900 transition-colors">
            <House size={16} weight="fill" />
          </button>
          <CaretRight size={14} className="text-slate-300" />
          <button
            onClick={() => navigate(-1)}
            className="hover:text-slate-900 transition-colors font-medium"
          >
            Search Results
          </button>
          {product.category && (
            <>
              <CaretRight size={14} className="text-slate-300" />
              <span className="font-medium">{product.category}</span>
            </>
          )}
          <CaretRight size={14} className="text-slate-300" />
          <span className="font-semibold text-slate-900 truncate max-w-[200px]">{product.product_name}</span>
        </nav>

        {/* Back + Share */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 text-sm font-semibold text-slate-600 border border-slate-200 px-3 py-1.5 rounded-xl hover:bg-slate-50 transition-all"
          >
            <ArrowLeft size={16} weight="bold" />
            <span className="hidden sm:inline">Back to Results</span>
          </button>
          <button className="flex items-center gap-1.5 text-sm font-semibold text-slate-600 border border-slate-200 px-3 py-1.5 rounded-xl hover:bg-slate-50 transition-all">
            <ShareNetwork size={16} />
            <span className="hidden sm:inline">Share</span>
          </button>
        </div>
      </div>

      {/* ── Main Product Layout ──────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl mx-auto px-6 pb-12 w-full space-y-10">
        <div className="bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-8">

          {/* ── Left: Gallery ──────────────────────────────────────── */}
          <div className="lg:col-span-5 space-y-4">
            {/* Main image */}
            <div className="relative aspect-square bg-slate-50 border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
              {!imgErrors[activeImgIdx] ? (
                <img
                  src={galleryImages[activeImgIdx]}
                  alt={product.product_name || 'Product'}
                  className="w-full h-full object-cover transition-all duration-300"
                  onError={() => setImgErrors((p) => ({ ...p, [activeImgIdx]: true }))}
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-100 text-5xl">📦</div>
              )}

              {/* Best Match badge */}
              <span className="absolute top-4 left-4 bg-emerald-500 text-white text-xs font-extrabold px-3 py-1 rounded-full">
                Best Match
              </span>

              {/* Wishlist */}
              <button
                onClick={() => setWishlisted(!wishlisted)}
                className="absolute top-4 right-4 w-9 h-9 bg-white rounded-full flex items-center justify-center shadow-md hover:bg-slate-50 transition-all"
              >
                <Heart
                  size={18}
                  weight={wishlisted ? 'fill' : 'regular'}
                  className={wishlisted ? 'text-red-500' : 'text-slate-400'}
                />
              </button>
            </div>

            {/* Thumbnails */}
            <div className="flex gap-3">
              {galleryImages.slice(0, 4).map((img, i) => (
                <button
                  key={i}
                  onClick={() => setActiveImgIdx(i)}
                  className={`
                    flex-1 aspect-square rounded-xl overflow-hidden border-2 bg-slate-50 transition-all
                    ${activeImgIdx === i ? 'border-blue-500 shadow-sm' : 'border-transparent hover:border-slate-200'}
                  `}
                >
                  <img src={img} alt={`View ${i + 1}`} className="w-full h-full object-cover" />
                </button>
              ))}
              {/* "+N more" thumbnail */}
              {galleryImages.length > 4 && (
                <button
                  className="flex-1 aspect-square rounded-xl overflow-hidden border-2 border-transparent bg-slate-100 flex items-center justify-center"
                  onClick={() => setActiveImgIdx(4)}
                >
                  <span className="text-sm font-bold text-slate-500">+{galleryImages.length - 4}</span>
                </button>
              )}
            </div>
          </div>

          {/* ── Center: Product Info ────────────────────────────────── */}
          <div className="lg:col-span-4 space-y-5">
            {/* Match badge */}
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-100 text-blue-700 text-xs font-extrabold rounded-full">
                <Sparkle size={12} weight="fill" />
                {matchPct}% Match
              </span>
              <span className="text-xs text-slate-500 font-medium">Highly relevant to your search</span>
            </div>

            {/* Name */}
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 leading-tight">
                {product.product_name}
              </h1>
              {product.attribute_summary && (
                <p className="text-sm text-slate-500 mt-1.5 font-medium">
                  {product.attribute_summary.split(',').slice(0, 2).join(', ')}
                </p>
              )}
            </div>

            {/* Rating */}
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
              <span className="text-sm font-bold text-blue-600 underline decoration-dotted cursor-pointer">
                {product.avg_rating?.toFixed(1) || '4.5'} ({product.review_count?.toLocaleString() || '0'} reviews)
              </span>
            </div>

            {/* Price */}
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-black text-slate-900">
                ₹{product.price?.toLocaleString('en-IN') || '—'}
              </span>
              <span className="text-sm font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 rounded-full px-2.5 py-0.5 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                In Stock
              </span>
            </div>

            {/* Description */}
            <p className="text-sm text-slate-500 leading-relaxed">
              {descriptionText}
            </p>

            {/* Attribute icons row */}
            {product.attribute_summary && (
              <div className="flex flex-wrap gap-4 py-3 border-y border-slate-100">
                {[
                  { icon: '🪑', label: 'Ergonomic Support' },
                  { icon: '💨', label: 'Breathable Mesh' },
                  { icon: '↕️', label: 'Adjustable Arms' },
                  { icon: '🛡️', label: '12-Year Warranty' },
                ].map((attr, i) => (
                  <div key={i} className="flex flex-col items-center gap-1 text-center min-w-[60px]">
                    <span className="text-xl">{attr.icon}</span>
                    <span className="text-[10px] text-slate-500 font-semibold leading-tight max-w-[64px]">{attr.label}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Key Features */}
            {keyFeatures.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-bold text-slate-900 text-sm">Key Features</h3>
                <div className="space-y-1.5">
                  {keyFeatures.map((feat, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm text-slate-600">
                      <CheckCircle size={16} weight="fill" className="text-blue-500 flex-shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
                <button className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 mt-2">
                  View full specifications
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </button>
              </div>
            )}

            {/* Review summary from Databricks */}
            {product.review_summary && (
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 text-xs text-slate-600 leading-relaxed">
                <span className="font-bold text-blue-700 block mb-1">Customer Review Summary (AI)</span>
                {product.review_summary}
              </div>
            )}
          </div>

          {/* ── Right: Options + CTA ────────────────────────────────── */}
          <div className="lg:col-span-3">
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-5 sticky top-24">
              <h3 className="font-extrabold text-slate-900 text-base">Select Options</h3>

              {/* Size */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">Size</span>
                  <span className="text-blue-500 text-xs">ⓘ</span>
                </div>
                <div className="flex gap-2">
                  {['A', 'B', 'C'].map((size) => (
                    <button
                      key={size}
                      onClick={() => setSelectedSize(size)}
                      className={`
                        px-4 py-2 text-sm font-bold rounded-xl border transition-all active:scale-95
                        ${selectedSize === size
                          ? 'bg-blue-600 border-blue-600 text-white shadow-sm'
                          : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                        }
                      `}
                    >
                      Size {size}
                    </button>
                  ))}
                </div>
              </div>

              {/* Frame */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">Frame / Base</span>
                <select
                  value={selectedFrame}
                  onChange={(e) => setSelectedFrame(e.target.value)}
                  className="w-full text-sm font-medium bg-white border border-slate-200 rounded-xl px-3 py-2.5 outline-none focus:border-blue-400"
                >
                  <option value="graphite">Graphite Frame / Graphite Base</option>
                  <option value="polished">Polished Aluminum</option>
                  <option value="mineral">Mineral Frame / Base</option>
                </select>
              </div>

              {/* Caster */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">Caster</span>
                <select
                  value={selectedCasters}
                  onChange={(e) => setSelectedCasters(e.target.value)}
                  className="w-full text-sm font-medium bg-white border border-slate-200 rounded-xl px-3 py-2.5 outline-none focus:border-blue-400"
                >
                  <option value="carpet">Carpet Casters</option>
                  <option value="hardfloor">Hard Floor Casters</option>
                </select>
              </div>

              {/* Price */}
              <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                <span className="text-sm font-bold text-slate-500">Price</span>
                <span className="text-xl font-black text-slate-900">
                  ₹{product.price?.toLocaleString('en-IN') || '—'}
                </span>
              </div>

              {/* CTAs */}
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold py-3 rounded-xl transition-all active:scale-95 shadow-md shadow-blue-200 flex items-center justify-center gap-2">
                <ShoppingCart size={16} />
                Add to Cart
              </button>
              <button className="w-full bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 text-sm font-bold py-3 rounded-xl transition-all active:scale-95">
                Buy Now
              </button>

              {/* Secure checkout */}
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3 flex gap-2.5">
                <ShieldCheck size={20} className="text-emerald-600 flex-shrink-0 mt-0.5" weight="fill" />
                <div>
                  <p className="text-xs font-bold text-slate-800">Secure & Trusted</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Encrypted payments • 30-day returns • Genuine products</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Related Products ─────────────────────────────────────── */}
        {product.related_products && product.related_products.length > 0 && (
          <div>
            <RelatedProducts products={product.related_products} />
          </div>
        )}

        {/* ── Value Proposition Footer Strip ───────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-0 bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm divide-y sm:divide-y-0 sm:divide-x divide-slate-100">
          <div className="py-8 flex flex-col items-center gap-3 text-center px-6">
            <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
              <Truck size={24} weight="fill" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-slate-900">Free Shipping</h4>
              <p className="text-xs text-slate-500 mt-1">On orders over ₹50</p>
            </div>
          </div>
          <div className="py-8 flex flex-col items-center gap-3 text-center px-6">
            <div className="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center text-purple-600">
              <ArrowCounterClockwise size={24} weight="fill" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-slate-900">30-Day Returns</h4>
              <p className="text-xs text-slate-500 mt-1">No hassle returns</p>
            </div>
          </div>
          <div className="py-8 flex flex-col items-center gap-3 text-center px-6">
            <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
              <SealCheck size={24} weight="fill" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-slate-900">12-Year Warranty</h4>
              <p className="text-xs text-slate-500 mt-1">Peace of mind guaranteed</p>
            </div>
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
