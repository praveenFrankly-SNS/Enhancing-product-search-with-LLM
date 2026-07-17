import { Sparkle, Lightning, Clock, Cpu } from '@phosphor-icons/react'

interface SearchMetaBarProps {
  totalResults: number
  processingTimeMs: number
  cached?: boolean
  query: string
  /** LLM-rewritten query from Databricks */
  rewrittenQuery?: string | null
  /** Key intent tokens extracted by LLM */
  intentTokens?: string[]
  /** Embedding model name from Databricks */
  modelName?: string | null
}

export function SearchMetaBar({
  totalResults,
  processingTimeMs,
  cached = false,
  query,
  rewrittenQuery,
  intentTokens = [],
  modelName,
}: SearchMetaBarProps) {
  // Fall back to basic token extraction if LLM tokens not available
  const displayTokens = intentTokens.length > 0
    ? intentTokens
    : query
        .toLowerCase()
        .split(' ')
        .filter((t) => t.length > 2 && !['and', 'for', 'with', 'under', 'the'].includes(t))
        .slice(0, 5)

  const displayModel = modelName || 'bge-large-en-v1.5'

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
      {/* Search Understanding */}
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0 text-blue-600">
          <Sparkle size={20} weight="fill" />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Search Understanding</p>
          <div className="flex flex-wrap gap-1 mt-1">
            {displayTokens.length > 0 ? (
              displayTokens.map((token, i) => (
                <span
                  key={i}
                  className="inline-block text-[11px] font-semibold text-blue-700 bg-blue-50 border border-blue-100 rounded px-1.5 py-0.5 truncate max-w-[90px]"
                  title={token}
                >
                  {token}
                </span>
              ))
            ) : (
              <span className="text-xs text-gray-500 font-medium">Semantic Query</span>
            )}
          </div>
          {rewrittenQuery && rewrittenQuery !== query && (
            <p className="text-[10px] text-gray-400 mt-1 italic truncate" title={rewrittenQuery}>
              "{rewrittenQuery}"
            </p>
          )}
        </div>
      </div>

      {/* Results Found */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center flex-shrink-0 text-green-600">
          <Lightning size={20} weight="fill" />
        </div>
        <div>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Results Found</p>
          <p className="text-sm font-bold text-gray-900 mt-0.5">
            {totalResults.toLocaleString()} products
          </p>
        </div>
      </div>

      {/* Search Time */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center flex-shrink-0 text-amber-600">
          <Clock size={20} weight="fill" />
        </div>
        <div>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Search Time</p>
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

      {/* Embedding Model */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0 text-blue-600">
          <Cpu size={20} weight="fill" />
        </div>
        <div>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Model</p>
          <p className="text-xs font-bold text-gray-700 mt-0.5 leading-snug" title={displayModel}>
            {displayModel}
          </p>
        </div>
      </div>
    </div>
  )
}
