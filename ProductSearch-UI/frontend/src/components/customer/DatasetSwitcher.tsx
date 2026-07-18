import { useState, useEffect } from 'react'
import { Database, ShoppingBag } from 'lucide-react'

export type DatasetVariant = 'wands' | 'amazon'

interface DatasetSwitcherProps {
  onDatasetChange?: (variant: DatasetVariant) => void
  className?: string
}

export function DatasetSwitcher({ onDatasetChange, className = '' }: DatasetSwitcherProps) {
  const [selected, setSelected] = useState<DatasetVariant>(() => {
    return (localStorage.getItem('dataset_variant') as DatasetVariant) || 'wands'
  })

  useEffect(() => {
    localStorage.setItem('dataset_variant', selected)
    if (onDatasetChange) {
      onDatasetChange(selected)
    }
  }, [selected])

  const handleToggle = (variant: DatasetVariant) => {
    setSelected(variant)
    window.dispatchEvent(new CustomEvent('datasetChanged', { detail: variant }))
  }

  return (
    <div className={`inline-flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 shadow-inner ${className}`}>
      <button
        onClick={() => handleToggle('wands')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
          selected === 'wands'
            ? 'bg-white text-blue-700 shadow-sm border border-slate-200'
            : 'text-slate-600 hover:text-slate-900'
        }`}
        title="WANDS Benchmark (30k products)"
      >
        <Database size={13} className={selected === 'wands' ? 'text-blue-600' : 'text-slate-400'} />
        <span>WANDS (30k)</span>
      </button>

      <button
        onClick={() => handleToggle('amazon')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
          selected === 'amazon'
            ? 'bg-amber-500 text-white shadow-sm shadow-amber-200'
            : 'text-slate-600 hover:text-slate-900'
        }`}
        title="Amazon Products (1.5k rich e-commerce items with real images & reviews)"
      >
        <ShoppingBag size={13} className={selected === 'amazon' ? 'text-white' : 'text-slate-400'} />
        <span>Amazon (1.5k)</span>
      </button>
    </div>
  )
}
