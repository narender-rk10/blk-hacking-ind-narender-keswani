import React, { useState, useCallback, useMemo } from 'react'
import toast from 'react-hot-toast'
import { transactionAPI } from '../services/api'
import useAppStore from '../store/appStore'
import JsonInput from './JsonInput'
import VirtualTable from './VirtualTable'
import CopyButton from './CopyButton'

const sampleExpenses = [
  { date: '2023-10-12 20:15:00', amount: 250 },
  { date: '2023-02-28 15:49:00', amount: 375 },
  { date: '2023-07-01 21:59:00', amount: 620 },
  { date: '2023-12-17 08:09:00', amount: 480 },
]

const columns = [
  { key: 'date', label: 'Date', width: '220px' },
  { key: 'amount', label: 'Amount', width: '120px' },
  { key: 'ceiling', label: 'Ceiling', width: '120px' },
  { key: 'remanent', label: 'Remanent', width: '120px' },
]

export default function TransactionParser() {
  const [expenses, setExpenses] = useState(null)
  const [result, setResult] = useState(null)
  const setTransactions = useAppStore((s) => s.setTransactions)
  const loading = useAppStore((s) => s.loading)
  const setLoading = useAppStore((s) => s.setLoading)

  const handleParsed = useCallback((data) => {
    setExpenses(data)
  }, [])

  const handleSubmit = useCallback(async () => {
    if (!expenses) return
    setLoading('parse', true)
    try {
      const { data } = await transactionAPI.parse(expenses)
      setResult(data)
      setTransactions(data)
      toast.success(`Parsed ${data.length} transactions`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to parse')
    } finally {
      setLoading('parse', false)
    }
  }, [expenses, setTransactions, setLoading])

  const totals = useMemo(() => {
    if (!result) return null
    return {
      totalAmount: result.reduce((s, t) => s + t.amount, 0).toFixed(2),
      totalCeiling: result.reduce((s, t) => s + t.ceiling, 0).toFixed(2),
      totalRemanent: result.reduce((s, t) => s + t.remanent, 0).toFixed(2),
    }
  }, [result])

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Transaction Parser</h2>
        <p className="text-gray-400 text-sm mt-1">
          Parse expenses into transactions with ceiling and remanent calculations
        </p>
      </div>

      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
        <JsonInput
          label="Expenses JSON (array of {date, amount})"
          placeholder='[{"date": "2023-10-12 20:15:00", "amount": 250}, ...]'
          onParsed={handleParsed}
          sampleData={sampleExpenses}
        />
        <div className="mt-4">
          <button
            onClick={handleSubmit}
            disabled={!expenses || loading.parse}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm transition"
          >
            {loading.parse ? 'Processing...' : 'Submit to API'}
          </button>
        </div>
      </div>

      {result && (
        <>
          {totals && (
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                <p className="text-xs text-gray-500 uppercase">Total Amount</p>
                <p className="text-xl font-bold text-white mt-1">{totals.totalAmount}</p>
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                <p className="text-xs text-gray-500 uppercase">Total Ceiling</p>
                <p className="text-xl font-bold text-white mt-1">{totals.totalCeiling}</p>
              </div>
              <div className="bg-gray-900/50 border border-emerald-900/50 rounded-xl p-4">
                <p className="text-xs text-emerald-500 uppercase">Total Remanent</p>
                <p className="text-xl font-bold text-emerald-400 mt-1">{totals.totalRemanent}</p>
              </div>
            </div>
          )}

          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white">Parsed Transactions</h3>
              <CopyButton text={result} />
            </div>
            <VirtualTable data={result} columns={columns} height={350} />
          </div>
        </>
      )}
    </div>
  )
}
