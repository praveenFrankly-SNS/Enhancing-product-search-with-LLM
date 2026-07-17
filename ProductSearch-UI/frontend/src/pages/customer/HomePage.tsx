import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { SearchBar } from '@/components/customer/SearchBar'
import { 
  Sparkle, 
  Lightning, 
  ShieldCheck, 
  TrendUp,
  ArrowRight 
} from '@phosphor-icons/react'

const POPULAR_SEARCHES = [
  'Gaming laptop',
  'Wireless headphones',
  'Office chair',
  'Smart watch',
  'Coffee maker',
  '4K monitor',
]

const SUGGESTED_CATEGORIES = [
  { name: 'Electronics', icon: '💻', color: 'from-blue-500 to-cyan-500' },
  { name: 'Fashion', icon: '👔', color: 'from-purple-500 to-pink-500' },
  { name: 'Home & Kitchen', icon: '🏠', color: 'from-orange-500 to-red-500' },
  { name: 'Sports', icon: '⚽', color: 'from-green-500 to-emerald-500' },
  { name: 'Beauty', icon: '💄', color: 'from-pink-500 to-rose-500' },
  { name: 'Books', icon: '📚', color: 'from-indigo-500 to-purple-500' },
]

export function HomePage() {
  const navigate = useNavigate()
  const [isSearching, setIsSearching] = useState(false)
  
  const handleSearch = (query: string) => {
    setIsSearching(true)
    navigate(`/search?q=${encodeURIComponent(query)}`)
  }
  
  const handlePopularSearch = (query: string) => {
    handleSearch(query)
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-primary-50/30">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center">
                <Sparkle size={24} weight="fill" className="text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Product Search
                </h1>
                <p className="text-xs text-gray-500">AI-Powered Discovery</p>
              </div>
            </div>
            
            <nav className="flex items-center gap-6">
              <a href="#features" className="text-sm font-medium text-gray-600 hover:text-primary-600 transition-colors">
                Features
              </a>
              <a href="/admin" className="text-sm font-medium text-gray-600 hover:text-primary-600 transition-colors">
                Dashboard
              </a>
            </nav>
          </div>
        </div>
      </header>
      
      {/* Hero Section */}
      <main className="container mx-auto px-4 py-12 md:py-20">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Hero Text */}
          <div className="space-y-4 animate-slide-up">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
              <Lightning size={16} weight="fill" />
              <span>Powered by Databricks Vector Search</span>
            </div>
            
            <h2 className="text-4xl md:text-6xl font-bold text-gray-900 leading-tight">
              Find Products Using
              <span className="bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                {' '}Natural Language
              </span>
            </h2>
            
            <p className="text-xl md:text-2xl text-gray-600 max-w-2xl mx-auto text-balance">
              Describe what you need in your own words. Our AI understands context and finds exactly what you're looking for.
            </p>
          </div>
          
          {/* Search Bar */}
          <div className="max-w-2xl mx-auto animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <SearchBar 
              onSearch={handleSearch}
              placeholder="Try: 'lightweight laptop for students' or 'ergonomic office chair'"
              autoFocus
              size="lg"
            />
            
            {/* Popular Searches */}
            <div className="mt-6 space-y-3">
              <p className="text-sm text-gray-500 font-medium">Popular searches:</p>
              <div className="flex flex-wrap justify-center gap-2">
                {POPULAR_SEARCHES.map((search, index) => (
                  <button
                    key={index}
                    onClick={() => handlePopularSearch(search)}
                    className="
                      px-4 py-2 bg-white border border-gray-200 rounded-full
                      text-sm font-medium text-gray-700
                      hover:border-primary-300 hover:text-primary-600
                      hover:shadow-sm
                      transition-all duration-200
                      focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                    "
                  >
                    {search}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          {/* Features Grid */}
          <div 
            className="grid md:grid-cols-3 gap-6 mt-16 animate-fade-in" 
            style={{ animationDelay: '0.4s' }}
            id="features"
          >
            <FeatureCard
              icon={<Sparkle size={32} weight="fill" className="text-primary-500" />}
              title="Semantic Understanding"
              description="Understands meaning and context, not just keywords"
            />
            <FeatureCard
              icon={<Lightning size={32} weight="fill" className="text-accent-500" />}
              title="Lightning Fast"
              description="Results in under 2-3 seconds with intelligent caching"
            />
            <FeatureCard
              icon={<ShieldCheck size={32} weight="fill" className="text-green-500" />}
              title="Enterprise Grade"
              description="Built on Databricks with Unity Catalog governance"
            />
          </div>
          
          {/* Categories */}
          <div className="mt-16 space-y-6 animate-fade-in" style={{ animationDelay: '0.6s' }}>
            <h3 className="text-2xl font-bold text-gray-900">Browse by Category</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {SUGGESTED_CATEGORIES.map((category, index) => (
                <button
                  key={index}
                  onClick={() => handleSearch(category.name)}
                  className="
                    group relative overflow-hidden
                    bg-white border-2 border-gray-200 rounded-2xl
                    p-6 text-center
                    hover:border-transparent hover:shadow-lg
                    transition-all duration-300
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                  "
                >
                  <div className={`
                    absolute inset-0 bg-gradient-to-br ${category.color}
                    opacity-0 group-hover:opacity-10 transition-opacity duration-300
                  `} />
                  <div className="relative space-y-2">
                    <div className="text-4xl">{category.icon}</div>
                    <div className="text-sm font-semibold text-gray-900">
                      {category.name}
                    </div>
                  </div>
                  <ArrowRight 
                    size={16} 
                    className="
                      absolute bottom-3 right-3
                      text-gray-400 group-hover:text-primary-500
                      opacity-0 group-hover:opacity-100
                      transform translate-x-2 group-hover:translate-x-0
                      transition-all duration-300
                    " 
                  />
                </button>
              ))}
            </div>
          </div>
          
          {/* Stats */}
          <div 
            className="mt-16 grid grid-cols-3 gap-8 pt-12 border-t border-gray-200 animate-fade-in"
            style={{ animationDelay: '0.8s' }}
          >
            <StatCard number="100K+" label="Products" />
            <StatCard number="<2s" label="Search Time" />
            <StatCard number="95%" label="Accuracy" />
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-20">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-sm text-gray-500">
            <p>Built with Databricks, FastAPI, and React</p>
            <p className="mt-2">Part of the Product Search Solution Accelerator</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ 
  icon, 
  title, 
  description 
}: { 
  icon: React.ReactNode
  title: string
  description: string 
}) {
  return (
    <div className="
      bg-white border border-gray-200 rounded-2xl p-6
      hover:shadow-soft hover:border-primary-200
      transition-all duration-300
      group
    ">
      <div className="space-y-3">
        <div className="
          w-16 h-16 bg-gradient-to-br from-gray-50 to-gray-100
          rounded-xl flex items-center justify-center
          group-hover:scale-110 transition-transform duration-300
        ">
          {icon}
        </div>
        <h4 className="text-lg font-semibold text-gray-900">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </div>
  )
}

function StatCard({ number, label }: { number: string; label: string }) {
  return (
    <div className="space-y-1">
      <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
        {number}
      </div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  )
}
