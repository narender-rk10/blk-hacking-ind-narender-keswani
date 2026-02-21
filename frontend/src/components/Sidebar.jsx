import React, { useCallback } from 'react'
import { FileText, CheckCircle, Filter, TrendingUp, Activity } from 'lucide-react'
import useAppStore from '../store/appStore'

const navItems = [
  { key: 'parser', label: 'Parse Expenses', icon: FileText },
  { key: 'validator', label: 'Validate', icon: CheckCircle },
  { key: 'filter', label: 'Q/P/K Filter', icon: Filter },
  { key: 'returns', label: 'Returns', icon: TrendingUp },
  { key: 'performance', label: 'Performance', icon: Activity },
]

export default function Sidebar() {
  const activeSection = useAppStore((s) => s.activeSection)
  const setActiveSection = useAppStore((s) => s.setActiveSection)

  const handleClick = useCallback(
    (key) => {
      setActiveSection(key)
    },
    [setActiveSection]
  )

  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-5 border-b border-gray-800">
        <h1 className="text-lg font-bold text-white">BlackRock</h1>
        <p className="text-xs text-gray-400 mt-1">Auto-Savings Platform</p>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => handleClick(key)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeSection === key
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
            }`}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-800">
        <p className="text-xs text-gray-500 text-center">v1.0.0 | Hackathon 2025</p>
      </div>
    </aside>
  )
}
