import React, { useState, useCallback, useMemo } from 'react'
import toast from 'react-hot-toast'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { returnsAPI } from '../services/api'
import useAppStore from '../store/appStore'
import JsonInput from './JsonInput'
import CopyButton from './CopyButton'

const sampleReturnsInput = {
  age: 29,
  wage: 50000,
  inflation: 5.5,
  q: [{ fixed: 0, start: '2023-07-01 00:00:00', end: '2023-07-31 23:59:00' }],
  p: [{ extra: 25, start: '2023-10-01 08:00:00', end: '2023-12-31 19:59:00' }],
  k: [
    { start: '2023-03-01 00:00:00', end: '2023-11-30 23:59:00' },
    { start: '2023-01-01 00:00:00', end: '2023-12-31 23:59:00' },
  ],
  transactions: [
    { date: '2023-10-12 20:15:00', amount: 250 },
    { date: '2023-02-28 15:49:00', amount: 375 },
    { date: '2023-07-01 21:59:00', amount: 620 },
    { date: '2023-12-17 08:09:00', amount: 480 },
  ],
}

export default function ReturnsCalculator() {
  const loading = useAppStore((s) => s.loading)
  const setLoading = useAppStore((s) => s.setLoading)
  const [inputData, setInputData] = useState(null)
  const [npsResult, setNpsResult] = useState(null)
  const [indexResult, setIndexResult] = useState(null)

  const handleParsed = useCallback((data) => {
    setInputData(data)
  }, [])

  const handleCalculate = useCallback(async () => {
    if (!inputData) {
      toast.error('Enter calculation input first')
      return
    }
    setLoading('returns', true)
    try {
      const [npsRes, indexRes] = await Promise.all([
        returnsAPI.nps(inputData),
        returnsAPI.index(inputData),
      ])
      setNpsResult(npsRes.data)
      setIndexResult(indexRes.data)
      toast.success('Returns calculated')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Calculation failed')
    } finally {
      setLoading('returns', false)
    }
  }, [inputData, setLoading])

  // Chart data: year-by-year growth comparison
  const chartData = useMemo(() => {
    if (!inputData || !npsResult) return []
    const age = inputData.age || 30
    const t = Math.max(60 - age, 5)
    const inflation = (inputData.inflation || 5.5) / 100
    // Use the first k period amount or total
    const principal =
      npsResult.savingsByDates?.length > 0
        ? npsResult.savingsByDates[npsResult.savingsByDates.length - 1].amount
        : 0
    const data = []
    for (let yr = 0; yr <= t; yr++) {
      const npsVal = principal * Math.pow(1.0711, yr) / Math.pow(1 + inflation, yr)
      const idxVal = principal * Math.pow(1.1449, yr) / Math.pow(1 + inflation, yr)
      data.push({
        year: yr,
        age: age + yr,
        NPS: Math.round(npsVal * 100) / 100,
        'Index Fund': Math.round(idxVal * 100) / 100,
      })
    }
    return data
  }, [inputData, npsResult])

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Returns Calculator</h2>
        <p className="text-gray-400 text-sm mt-1">
          Compare NPS vs NIFTY 50 Index Fund with inflation-adjusted projections
        </p>
      </div>

      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
        <JsonInput
          label="Full Calculation Input"
          placeholder='{"age": 29, "wage": 50000, "inflation": 5.5, "q": [...], "p": [...], "k": [...], "transactions": [...]}'
          onParsed={handleParsed}
          sampleData={sampleReturnsInput}
        />
        <div className="mt-4">
          <button
            onClick={handleCalculate}
            disabled={!inputData || loading.returns}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm transition"
          >
            {loading.returns ? 'Calculating...' : 'Calculate Returns'}
          </button>
        </div>
      </div>

      {npsResult && indexResult && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
              <p className="text-xs text-gray-500 uppercase">Total Expense Amount</p>
              <p className="text-xl font-bold text-white mt-1">
                {npsResult.transactionsTotalAmount?.toLocaleString()}
              </p>
            </div>
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
              <p className="text-xs text-gray-500 uppercase">Total Ceiling</p>
              <p className="text-xl font-bold text-white mt-1">
                {npsResult.transactionsTotalCeiling?.toLocaleString()}
              </p>
            </div>
          </div>

          {/* K-Period Results */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* NPS Results */}
            <div className="bg-gray-900/50 border border-blue-900/30 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-blue-400">NPS Returns (7.11%)</h3>
                <CopyButton text={npsResult} />
              </div>
              {npsResult.savingsByDates?.map((s, i) => (
                <div key={i} className="mb-3 p-3 bg-gray-800/50 rounded-lg">
                  <p className="text-xs text-gray-500">
                    {s.start} to {s.end}
                  </p>
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    <div>
                      <p className="text-xs text-gray-500">Invested</p>
                      <p className="text-sm font-bold text-white">{s.amount}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Profit</p>
                      <p className="text-sm font-bold text-emerald-400">{s.profit}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Tax Benefit</p>
                      <p className="text-sm font-bold text-yellow-400">{s.taxBenefit}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Index Results */}
            <div className="bg-gray-900/50 border border-emerald-900/30 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-emerald-400">
                  Index Fund Returns (14.49%)
                </h3>
                <CopyButton text={indexResult} />
              </div>
              {indexResult.savingsByDates?.map((s, i) => (
                <div key={i} className="mb-3 p-3 bg-gray-800/50 rounded-lg">
                  <p className="text-xs text-gray-500">
                    {s.start} to {s.end}
                  </p>
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    <div>
                      <p className="text-xs text-gray-500">Invested</p>
                      <p className="text-sm font-bold text-white">{s.amount}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Profit</p>
                      <p className="text-sm font-bold text-emerald-400">{s.profit}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Tax Benefit</p>
                      <p className="text-sm font-bold text-gray-500">{s.taxBenefit}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Growth Chart */}
          {chartData.length > 0 && (
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
              <h3 className="font-semibold text-white mb-4">
                Growth Projection (Inflation-Adjusted)
              </h3>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="year"
                    stroke="#666"
                    label={{ value: 'Years', position: 'insideBottom', offset: -5, fill: '#888' }}
                  />
                  <YAxis stroke="#666" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e1e2e',
                      border: '1px solid #333',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="NPS"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="Index Fund"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  )
}
