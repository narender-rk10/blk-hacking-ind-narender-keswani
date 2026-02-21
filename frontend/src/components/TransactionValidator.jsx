import React, { useState, useCallback, useMemo } from 'react'
import toast from 'react-hot-toast'
import { transactionAPI } from '../services/api'
import useAppStore from '../store/appStore'
import VirtualTable from './VirtualTable'
import CopyButton from './CopyButton'

const validColumns = [
  { key: 'date', label: 'Date', width: '220px' },
  { key: 'amount', label: 'Amount', width: '120px' },
  { key: 'ceiling', label: 'Ceiling', width: '120px' },
  { key: 'remanent', label: 'Remanent', width: '120px' },
]

const invalidColumns = [
  ...validColumns,
  { key: 'message', label: 'Error', width: '250px' },
]

export default function TransactionValidator() {
  const transactions = useAppStore((s) => s.transactions)
  const loading = useAppStore((s) => s.loading)
  const setLoading = useAppStore((s) => s.setLoading)
  const setValidationResult = useAppStore((s) => s.setValidationResult)
  const validTransactions = useAppStore((s) => s.validTransactions)
  const invalidTransactions = useAppStore((s) => s.invalidTransactions)
  const [wage, setWage] = useState(50000)
  const [result, setResult] = useState(null)

  const handleValidate = useCallback(async () => {
    if (!transactions.length) {
      toast.error('Parse expenses first')
      return
    }
    setLoading('validate', true)
    try {
      const { data } = await transactionAPI.validate({
        wage,
        transactions,
      })
      setResult(data)
      setValidationResult(data.valid || [], data.invalid || [])
      toast.success(
        `${(data.valid || []).length} valid, ${(data.invalid || []).length} invalid`
      )
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Validation failed')
    } finally {
      setLoading('validate', false)
    }
  }, [transactions, wage, setLoading, setValidationResult])

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Transaction Validator</h2>
        <p className="text-gray-400 text-sm mt-1">
          Validate transactions based on wage and business rules
        </p>
      </div>

      <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 space-y-4">
        <div>
          <label className="text-sm font-medium text-gray-300">Monthly Wage (INR)</label>
          <input
            type="number"
            value={wage}
            onChange={(e) => setWage(Number(e.target.value))}
            className="mt-1 w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500"
          />
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleValidate}
            disabled={!transactions.length || loading.validate}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium text-sm transition"
          >
            {loading.validate ? 'Validating...' : 'Validate Transactions'}
          </button>
          <span className="text-sm text-gray-500">
            {transactions.length} transactions loaded
          </span>
        </div>
      </div>

      {result && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-900/50 border border-emerald-900/50 rounded-xl p-4">
              <p className="text-xs text-emerald-500 uppercase">Valid</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">
                {(result.valid || []).length}
              </p>
            </div>
            <div className="bg-gray-900/50 border border-red-900/50 rounded-xl p-4">
              <p className="text-xs text-red-500 uppercase">Invalid</p>
              <p className="text-2xl font-bold text-red-400 mt-1">
                {(result.invalid || []).length}
              </p>
            </div>
          </div>

          {result.valid?.length > 0 && (
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-emerald-400">Valid Transactions</h3>
                <CopyButton text={result.valid} />
              </div>
              <VirtualTable data={result.valid} columns={validColumns} height={250} />
            </div>
          )}

          {result.invalid?.length > 0 && (
            <div className="bg-gray-900/50 border border-red-900/30 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-red-400">Invalid Transactions</h3>
                <CopyButton text={result.invalid} />
              </div>
              <VirtualTable data={result.invalid} columns={invalidColumns} height={200} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
