import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { SearchBar } from '@/components/customer/SearchBar'
import { DatasetSwitcher } from '@/components/customer/DatasetSwitcher'
import { searchAPI } from '@/services/api'
import {
  Sparkles,
  Target,
  Zap,
  Shield,
  Globe,
  User,
} from 'lucide-react'

// Wireframe-matching suggestion chips
const SUGGESTION_CHIPS = [
  'Gaming laptop under $1500',
  'Ergonomic office chair',
  'Smart watch with health tracking',
  'Espresso coffee machine',
  '4K monitor for design',
]

// Features matching the wireframe feature strip
const FEATURES = [
  {
    icon: <Sparkles size={24} className="text-blue-600" />,
    bg: 'bg-blue-50',
    title: 'Semantic Understanding',
    desc: 'Search naturally, like you talk',
  },
  {
    icon: <Target size={24} className="text-purple-600" />,
    bg: 'bg-purple-50',
    title: 'More Relevant Results',
    desc: 'Powered by AI embeddings',
  },
  {
    icon: <Zap size={24} className="text-amber-500" />,
    bg: 'bg-amber-50',
    title: 'Fast & Accurate',
    desc: 'Results in under 2 seconds',
  },
  {
    icon: <Shield size={24} className="text-orange-500" />,
    bg: 'bg-orange-50',
    title: 'Secure & Governed',
    desc: 'Enterprise-grade on Databricks',
  },
]

// Static category images that match the wireframe categories
const CATEGORY_IMAGES: Record<string, string> = {
  'Laptops': 'https://images.unsplash.com/photo-1496181130204-755241544e35?auto=format&fit=crop&w=400&q=80',
  'Audio': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=400&q=80',
  'Smart Watches': 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=400&q=80',
  'Home & Kitchen': 'https://images.unsplash.com/photo-1588854337236-6889d631faa8?auto=format&fit=crop&w=400&q=80',
  'Office Furniture': 'https://images.unsplash.com/photo-1505797149-43b0069ec26b?auto=format&fit=crop&w=400&q=80',
  'Monitors': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=400&q=80',
  'Office Chairs': 'https://images.unsplash.com/photo-1505797149-43b0069ec26b?auto=format&fit=crop&w=400&q=80',
  'Headphones': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=400&q=80',
}

const DEFAULT_IMG = 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=400&q=80'

export function HomePage() {
  const navigate = useNavigate()

  // Fetch live categories from Databricks Gold table
  const { data: categories = [], isLoading: catsLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: searchAPI.getCategories,
    staleTime: 5 * 60 * 1000,
  })

  const handleSearch = (query: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}`)
  }

  // Show top 6 categories
  const displayCategories = categories.slice(0, 6)

  return (
    <div className="min-h-screen bg-white flex flex-col font-sans">
      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <header className="border-b border-slate-100 bg-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-md shadow-blue-200">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-white">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <p className="text-[15px] font-extrabold text-slate-900 leading-none">ProductSearch</p>
              <p className="text-[10px] text-slate-400 font-semibold leading-none mt-0.5">Databricks Accelerator</p>
            </div>
          </div>

          {/* Nav links */}
          <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-slate-600">
            <a href="/" className="text-slate-900 border-b-2 border-blue-600 pb-0.5">Home</a>
            <a href="#about" className="hover:text-slate-900 transition-colors">About</a>
            <a href="#how-it-works" className="hover:text-slate-900 transition-colors">How it Works</a>
            <a href="#help" className="hover:text-slate-900 transition-colors">Help</a>
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-3">
            <DatasetSwitcher />
            <button className="flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors">
              <Globe size={16} />
              <span className="hidden sm:inline">English</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── Hero Section ───────────────────────────────────────────────── */}
      <section className="bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-16 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left: Text + Search */}
          <div className="space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-white border border-slate-200 rounded-full shadow-sm text-xs font-bold text-slate-700">
              <Sparkles size={13} className="text-blue-600" />
              <span>AI-Powered Semantic Search</span>
            </div>

            {/* Headline */}
            <div className="space-y-2">
              <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 leading-tight">
                Find the Perfect Product,
              </h1>
              <h1 className="text-4xl md:text-5xl font-extrabold text-blue-600 leading-tight">
                Just by Describing It
              </h1>
            </div>

            <p className="text-lg text-slate-500 leading-relaxed max-w-xl">
              Search in natural language and discover products smarter, faster and more relevant than ever.
            </p>

            {/* Search Bar */}
            <div className="max-w-2xl">
              <SearchBar
                onSearch={handleSearch}
                placeholder='Try "lightweight laptop for remote work", "noise cancelling wireless headphones"...'
                size="lg"
                autoFocus
              />
            </div>

            {/* Suggestion chips */}
            <div className="flex flex-wrap gap-2 items-center">
              <div className="flex items-center gap-1.5 text-sm font-semibold text-slate-500">
                <Sparkles size={14} className="text-blue-500" />
                <span>Try these searches:</span>
              </div>
              {SUGGESTION_CHIPS.map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSearch(chip)}
                  className="px-3.5 py-1.5 bg-white border border-slate-200 hover:border-blue-400 hover:text-blue-700 rounded-full text-sm font-medium text-slate-700 transition-all active:scale-95 shadow-sm"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          {/* Right: Hero image collage */}
          <div className="hidden lg:block relative">
            <div className="absolute -inset-4 bg-gradient-to-tr from-blue-100/40 to-indigo-100/40 rounded-3xl blur-2xl" />
            <div className="relative rounded-3xl overflow-hidden shadow-2xl">
              <img
                src="https://images.unsplash.com/photo-1550009158-9ebf69173e03?auto=format&fit=crop&w=900&q=80"
                alt="Product Collection"
                className="w-full h-[380px] object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ── Feature Strip ──────────────────────────────────────────────── */}
      <section className="border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-0 divide-x divide-slate-100">
            {FEATURES.map((f, i) => (
              <div key={i} className="flex items-center gap-4 px-8 py-4">
                <div className={`w-11 h-11 rounded-xl ${f.bg} flex items-center justify-center flex-shrink-0`}>
                  {f.icon}
                </div>
                <div>
                  <p className="font-bold text-slate-900 text-sm">{f.title}</p>
                  <p className="text-xs text-slate-500">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Browse Popular Categories ───────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-14 w-full">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-extrabold text-slate-900">Browse Popular Categories</h2>
          <button className="text-sm font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1">
            View all categories
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
          </button>
        </div>

        {catsLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-5">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="rounded-2xl overflow-hidden border border-slate-100 animate-pulse">
                <div className="aspect-[4/3] bg-slate-100" />
                <div className="p-4 space-y-2">
                  <div className="h-3 bg-slate-100 rounded w-3/4" />
                  <div className="h-2 bg-slate-100 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-5">
            {displayCategories.map((cat, i) => (
              <button
                key={i}
                onClick={() => handleSearch(cat.name)}
                className="bg-white border border-slate-200 rounded-2xl overflow-hidden hover:border-blue-400 hover:shadow-lg transition-all duration-200 text-left group flex flex-col"
              >
                <div className="aspect-[4/3] bg-slate-50 relative overflow-hidden">
                  <img
                    src={CATEGORY_IMAGES[cat.name] ?? DEFAULT_IMG}
                    alt={cat.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <div className="p-4">
                  <h3 className="font-bold text-sm text-slate-900 group-hover:text-blue-600 transition-colors">
                    {cat.name}
                  </h3>
                  <p className="text-[11px] text-slate-400 font-semibold mt-0.5">
                    {cat.count.toLocaleString()}+ products
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="bg-slate-50 border-t border-slate-200 mt-auto">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-600">
            <div className="w-6 h-6 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-md flex items-center justify-center">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" className="text-white">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="font-bold text-slate-800">Built on Databricks</span>
            <span className="text-slate-300">|</span>
            <span className="text-slate-500">Powered by Unity Catalog, Vector Search, and MLflow</span>
          </div>
          <p className="text-xs text-slate-400">© {new Date().getFullYear()} Databricks Retail Accelerator</p>
        </div>
      </footer>
    </div>
  )
}
