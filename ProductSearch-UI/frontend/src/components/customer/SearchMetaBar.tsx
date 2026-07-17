import { Lightning, Sparkle, Clock, Cpu } from '@phosphor-icons/react'

interface SearchMetaBarProps {
  totalResults: number
  processingTimeMs: number
  cached?: boolean
  query: string
}

export function SearchMetaBar({
  totalResults,
  processingTimeMs,
  cached = false,
  query,
}: SearchMetaBarProps) {
  // Mock search token analysis for presentation
  const tokens = query
    .toLowerCase()
    .split(' ')
    .filter((t) => t.length > 2 && !['and', 'for', 'with', 'under', 'the'].includes(t))

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
      {/* Search Understanding */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center flex-shrink-0 text-primary-600">
          <Sparkle size={20} weight="fill" />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Search Intent</p>
          <div className="flex flex-wrap gap-1 mt-0.5">
            {tokens.length > 0 ? (
              tokens.map((token, i) => (
                <span
                  key={i}
                  className="inline-block text-[11px] font-semibold text-primary-700 bg-primary-50 border border-primary-100 rounded px-1.5 py-0.5 truncate max-w-[80px]"
                >
                  {token}
                </span>
              ))
            ) : (
              <span className="text-xs text-gray-500 font-medium">Semantic Query</span>
            )}
          </div>
        </div>
      </div>

      {/* Results Found */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center flex-shrink-0 text-purple-600">
          <Lightning size={20} weight="fill" />
        </div>
        <div>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Matches Found</p>
          <p className="text-sm font-bold text-gray-900 mt-0.5">
            {totalResults.toLocaleString()} Products
          </p>
        </div>
      </div>

      {/* Search Latency */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center flex-shrink-0 text-amber-600">
          <Clock size={20} weight="fill" />
        </div>
        <div>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Search Latency</p>
          <p className="text-sm font-bold text-gray-900 mt-0.5 flex items-center gap-1.5">
            <span>{processingTimeMs} ms</span>
            {cached && (
              <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.5 rounded">
                CACHED
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Model Name */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0 text-blue-600">
          <Cpu size={20} weight="fill" />
        </div>
        <div>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Embedding Model</p>
          <p className="text-xs font-bold text-gray-700 mt-0.5 leading-snug truncate max-w-[150px]" title="bge-large-en-v1.5">
            bge-large-en-v1.5
          </p>
        </div>
      </div>
    </div>
  )
}
