import { create } from 'zustand'

const useAppStore = create((set) => ({
  // Parsed transactions cache
  transactions: [],
  setTransactions: (t) => set({ transactions: t }),

  // Validation results
  validTransactions: [],
  invalidTransactions: [],
  setValidationResult: (valid, invalid) =>
    set({ validTransactions: valid, invalidTransactions: invalid }),

  // Filter results
  filterResult: null,
  setFilterResult: (r) => set({ filterResult: r }),

  // Returns results
  npsResult: null,
  indexResult: null,
  setReturnsResult: (type, result) =>
    set({ [`${type}Result`]: result }),

  // Active section
  activeSection: 'parser',
  setActiveSection: (s) => set({ activeSection: s }),

  // Loading states
  loading: {},
  setLoading: (key, val) =>
    set((state) => ({ loading: { ...state.loading, [key]: val } })),

  // Performance metrics
  performanceMetrics: null,
  setPerformanceMetrics: (m) => set({ performanceMetrics: m }),
}))

export default useAppStore
