import React, { useState, useCallback, useEffect } from 'react'
import { Clock, Cpu, HardDrive } from 'lucide-react'
import { performanceAPI } from '../services/api'
import useAppStore from '../store/appStore'

export default function PerformanceDashboard() {
  const [metrics, setMetrics] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(false)

  const fetchMetrics = useCallback(async () => {
    try {
      const { data } = await performanceAPI.get()
      setMetrics(data)
    } catch {
      // silent fail
    }
  }, [])

  useEffect(() => {
    fetchMetrics()
  }, [fetchMetrics])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(fetchMetrics, 2000)
    return () => clearInterval(interval)
  }, [autoRefresh, fetchMetrics])

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Performance Dashboard</h2>
          <p className="text-gray-400 text-sm mt-1">
            Real-time system execution metrics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-refresh (2s)
          </label>
          <button
            onClick={fetchMetrics}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {metrics ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-blue-600/20 rounded-lg">
                <Clock size={24} className="text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Uptime</p>
                <p className="text-2xl font-bold text-white">{metrics.time}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Server running since startup
            </p>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-emerald-600/20 rounded-lg">
                <HardDrive size={24} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Memory Usage</p>
                <p className="text-2xl font-bold text-white">{metrics.memory}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              RSS memory of the server process
            </p>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-purple-600/20 rounded-lg">
                <Cpu size={24} className="text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Threads</p>
                <p className="text-2xl font-bold text-white">{metrics.threads}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Active threads in the process
            </p>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <p>Unable to connect to backend. Make sure the API is running on port 5477.</p>
        </div>
      )}

      {/* API Endpoint Reference */}
      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-4">API Endpoints</h3>
        <div className="space-y-2">
          {[
            { method: 'POST', path: '/blackrock/challenge/v1/transactions:parse', desc: 'Parse expenses' },
            { method: 'POST', path: '/blackrock/challenge/v1/transactions:validator', desc: 'Validate transactions' },
            { method: 'POST', path: '/blackrock/challenge/v1/transactions:filter', desc: 'Apply q/p/k filters' },
            { method: 'POST', path: '/blackrock/challenge/v1/returns:nps', desc: 'NPS returns' },
            { method: 'POST', path: '/blackrock/challenge/v1/returns:index', desc: 'Index fund returns' },
            { method: 'GET', path: '/blackrock/challenge/v1/performance', desc: 'System metrics' },
          ].map(({ method, path, desc }) => (
            <div key={path} className="flex items-center gap-3 py-2 border-b border-gray-800 last:border-0">
              <span
                className={`text-xs font-mono px-2 py-1 rounded ${
                  method === 'GET' ? 'bg-blue-900/30 text-blue-400' : 'bg-emerald-900/30 text-emerald-400'
                }`}
              >
                {method}
              </span>
              <code className="text-sm text-gray-300 font-mono">{path}</code>
              <span className="text-xs text-gray-500 ml-auto">{desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
