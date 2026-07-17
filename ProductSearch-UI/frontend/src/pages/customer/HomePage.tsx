import { useNavigate } from 'react-router-dom'
import { SearchBar } from '@/components/customer/SearchBar'
import {
  Sparkle,
  Lightning,
  ShieldCheck,
  Cpu,
  BookmarkSimple
} from '@phosphor-icons/react'

const POPULAR_SEARCHES = [
  { text: 'Gaming laptop under ₹80,000', icon: '💻' },
  { text: 'Ergonomic office chair for back pain', icon: '🪑' },
  { text: 'Smart watch with health tracking', icon: '⌚' },
  { text: 'Espresso coffee machine with milk frother', icon: '☕' },
  { text: '4K monitor for designers', icon: '🖥️' },
]

const FEATURE_TILES = [
  {
    title: 'Semantic Understanding',
    desc: 'Search naturally, like you talk. The LLM translates user intent into dense vectors.',
    icon: <Sparkle size={24} className="text-primary-600" weight="fill" />,
    bg: 'bg-primary-50'
  },
  {
    title: 'More Relevant Results',
    desc: 'Powered by state-of-the-art AI embeddings synced across table updates.',
    icon: <BookmarkSimple size={24} className="text-purple-600" weight="fill" />,
    bg: 'bg-purple-50'
  },
  {
    title: 'Fast & Accurate',
    desc: 'Results in under 2 seconds. Powered by Databricks Serverless scaling.',
    icon: <Lightning size={24} className="text-amber-600" weight="fill" />,
    bg: 'bg-amber-50'
  },
  {
    title: 'Secure & Governed',
    desc: 'Enterprise-grade row/column governance powered by Unity Catalog.',
    icon: <ShieldCheck size={24} className="text-emerald-600" weight="fill" />,
    bg: 'bg-emerald-50'
  }
]

const CATEGORIES = [
  { name: 'Laptops', count: '1,247+ products', img: 'https://images.unsplash.com/photo-1496181130204-755241544e35?auto=format&fit=crop&w=400&q=80' },
  { name: 'Audio', count: '856+ products', img: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=400&q=80' },
  { name: 'Smart Watches', count: '423+ products', img: 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=400&q=80' },
  { name: 'Home & Kitchen', count: '1,120+ products', img: 'https://images.unsplash.com/photo-1588854337236-6889d631faa8?auto=format&fit=crop&w=400&q=80' },
  { name: 'Office Furniture', count: '678+ products', img: 'https://images.unsplash.com/photo-1505797149-43b0069ec26b?auto=format&fit=crop&w=400&q=80' },
  { name: 'Monitors', count: '564+ products', img: 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=400&q=80' },
]

export function HomePage() {
  const navigate = useNavigate()

  const handleSearch = (query: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 flex flex-col font-sans">
      {/* Navbar Header */}
      <header className="border-b border-slate-100 bg-white/70 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center shadow-md shadow-primary-200">
              <Sparkle size={22} weight="fill" className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-extrabold text-slate-900 leading-none flex items-center gap-1.5">
                <span>ProductSearch</span>
                <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded tracking-wider">
                  V2
                </span>
              </h1>
              <p className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider mt-0.5">
                Databricks Accelerator
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-6 text-sm font-semibold text-slate-600">
            <a href="/" className="text-primary-600">Home</a>
            <a href="#about" className="hover:text-primary-600 transition-colors">About</a>
            <a href="#how-it-works" className="hover:text-primary-600 transition-colors">How it Works</a>
            <span className="h-4 w-px bg-slate-200" />
            <button className="flex items-center gap-1.5 px-4 py-2 bg-slate-50 rounded-xl border border-slate-200/60 hover:bg-slate-100 transition-all active:scale-95 text-slate-800">
              <Cpu size={16} />
              <span>Dashboard</span>
            </button>
          </nav>
        </div>
      </header>

      {/* Main Hero & Search Block */}
      <main className="flex-1 max-w-7xl mx-auto px-6 w-full py-12 md:py-20 space-y-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Hero block */}
          <div className="lg:col-span-7 space-y-8 text-left">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-primary-50 border border-primary-100 rounded-full text-xs font-bold text-primary-700">
              <Sparkle size={14} weight="fill" />
              <span>AI-Powered Semantic Search</span>
            </div>

            <h2 className="text-4xl md:text-6xl font-extrabold text-slate-950 leading-tight font-display tracking-tight">
              Find the Perfect Product, <br />
              <span className="bg-gradient-to-r from-primary-600 to-indigo-600 bg-clip-text text-transparent">
                Just by Describing It
              </span>
            </h2>

            <p className="text-lg text-slate-500 max-w-xl leading-relaxed">
              Search in natural language and discover products smarter, faster, and more relevant than ever. Our semantic search understands the context, intent, and synonyms automatically.
            </p>

            {/* Search Input Widget */}
            <div className="max-w-xl">
              <SearchBar
                onSearch={handleSearch}
                placeholder="Try 'lightweight laptop for remote work' or 'ergonomic chair'..."
                size="lg"
                autoFocus
              />
            </div>

            {/* Try These Suggestions */}
            <div className="space-y-2.5">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Try these searches:</p>
              <div className="flex flex-wrap gap-2">
                {POPULAR_SEARCHES.map((chip, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSearch(chip.text)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 hover:border-primary-400 hover:text-primary-700 rounded-full text-xs font-semibold text-slate-700 transition-all active:scale-95 shadow-sm"
                  >
                    <span>{chip.icon}</span>
                    <span>{chip.text}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Imagery block */}
          <div className="lg:col-span-5 hidden lg:block relative">
            <div className="absolute inset-0 bg-gradient-to-tr from-primary-200/30 to-purple-200/30 rounded-3xl blur-2xl -z-10" />
            <div className="relative border border-slate-100 shadow-2xl rounded-3xl overflow-hidden aspect-[4/3] bg-slate-50">
              <img
                src="https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80"
                alt="Premium Home Office Office Setup"
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-6 left-6 right-6 bg-white/80 backdrop-blur-md border border-white/50 p-4 rounded-2xl shadow-xl flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Featured Index</p>
                  <p className="text-sm font-bold text-slate-800">product_search_catalog</p>
                </div>
                <div className="flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-100/80 px-2.5 py-1 rounded-full">
                  <Lightning size={12} weight="fill" />
                  <span>Sync Online</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 border-t border-slate-100 pt-16">
          {FEATURE_TILES.map((card, i) => (
            <div
              key={i}
              className="bg-white border border-slate-200/60 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200 group"
            >
              <div className={`w-12 h-12 rounded-xl ${card.bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200`}>
                {card.icon}
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1">{card.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{card.desc}</p>
            </div>
          ))}
        </div>

        {/* Popular Categories */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-2xl font-bold text-slate-950 font-display">Browse Popular Categories</h3>
            <button className="text-sm font-bold text-primary-600 hover:text-primary-700">
              View all categories
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {CATEGORIES.map((cat, i) => (
              <button
                key={i}
                onClick={() => handleSearch(cat.name)}
                className="bg-white border border-slate-200/60 rounded-2xl overflow-hidden hover:border-primary-400 hover:shadow-md transition-all duration-200 text-left group flex flex-col"
              >
                <div className="aspect-[4/3] bg-slate-50 relative overflow-hidden">
                  <img
                    src={cat.img}
                    alt={cat.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <div className="p-4 flex-1 flex flex-col justify-between">
                  <h4 className="font-bold text-sm text-slate-900 group-hover:text-primary-600 transition-colors">
                    {cat.name}
                  </h4>
                  <p className="text-[11px] text-slate-400 font-semibold mt-1">
                    {cat.count}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-8 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-semibold">
          <div className="flex items-center gap-2">
            <Sparkle size={16} className="text-primary-500" />
            <span className="text-slate-300 font-bold">Built on Databricks</span>
            <span className="text-slate-600">|</span>
            <span>Powered by Unity Catalog, Vector Search, and MLflow</span>
          </div>
          <div>
            © {new Date().getFullYear()} Databricks Retail Accelerator
          </div>
        </div>
      </footer>
    </div>
  )
}
