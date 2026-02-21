import React, { useState, useCallback } from 'react'
import toast from 'react-hot-toast'
import { transactionAPI } from '../services/api'
import useAppStore from '../store/appStore'
import JsonInput from './JsonInput'
import VirtualTable from './VirtualTable'
import CopyButton from './CopyButton'

const sampleFilter = {
  q: [{ fixed: 0, start: '2023-07-01 00:00:00', end: '2023-07-31 23:59:00' }],
  p: [{ extra: 25, start: '2023-10-01 08:00:00', end: '2023-12-31 19:59:00' }],
  k: [
    { start: '2023-03-01 00:00:00', end: '2023-11-30 23:59:00' },
    { start: '2023-01-01 00:00:00', end: '2023-12-31 23:59:00' },
  ],
}

const txnColumns = [
  { key: 'date', label: 'Date', width: '220px' },
  { key: 'amount', label: 'Amount', width: '110px' },
  { key: 'ceiling', label: 'Ceiling', width: '110px' },
  { key: 'remanent', label: 'Remanent', width: '110px' },
]

const kColumns = [
  { key: 'start', label: 'Start', width: '220px' },
  { key: 'end', label: 'End', width: '220px' },
  { key: 'amount', label: 'Amount', width: '120px' },
]

export default function TemporalFilter() {
  const transactions = useAppStore((s) => s.transactions)
  const loading = useAppStore((s) => s.loading)
  const setLoading = useAppStore((s) => s.setLoading)
  const setFilterResult = useAppStore((s) => s.setFilterResult)
  const [filterConfig, setFilterConfig] = useState(null)
  const [result, setResult] = useState(null)

  const handleParsed = useCallback((data) => {
    setFilterConfig(data)
  }, [])

  const handleFilter = useCallback(async () => {
    if (!transactions.length) {
      toast.error('Parse expenses first')
      return
    }
    if (!filterConfig) {
      toast.error('Enter q/p/k configuration')
      return
    }
    setLoading('filter', true)
    try {
      const payload = {
        ...filterConfig,
        transactions,
      }
      const { data } = await transactionAPI.filter(payload)
      setResult(data)
      setFilterResult(data)
      toast.success('Filters applied successfully')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Filter failed')
    } finally {
      setLoading('filter', false)
    }
  }, [transactions, filterConfig, setLoading, setFilterResult])

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Temporal Constraints Filter</h2>
        <p className="text-gray-400 text-sm mt-1">
          Apply q (fixed), p (extra), and k (grouping) period filters
        </p>
      </div>

      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
        <JsonInput
          label="Q/P/K Configuration JSON"
          placeholder='{"q": [...], "p": [...], "k": [...]}'
          onParsed={handleParsed}
          sampleData={sampleFilter}
        />
        <div className="mt-4">
          <button
            onClick={handleFilter}
            disabled={!transactions.length || !filterConfig || loading.filter}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm transition"
          >
            {loading.filter ? 'Processing...' : 'Apply Filters'}
          </button>
        </div>
      </div>

      {result && (
        <>
          {result.valid?.length > 0 && (
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white">
                  Processed Transactions (after q/p)
                </h3>
                <CopyButton text={result.valid} />
              </div>
              <VirtualTable data={result.valid} columns={txnColumns} height={250} />
            </div>
          )}

          {result.k_results?.length > 0 && (
            <div className="bg-gray-900/50 border border-blue-900/30 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-blue-400">K Period Results</h3>
                <CopyButton text={result.k_results} />
              </div>
              <VirtualTable data={result.k_results} columns={kColumns} height={200} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
