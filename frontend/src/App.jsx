import React, { Suspense, lazy } from 'react'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/Sidebar'
import LoadingSpinner from './components/LoadingSpinner'
import useAppStore from './store/appStore'

// Lazy loading — only download what user navigates to
const TransactionParser = lazy(() => import('./components/TransactionParser'))
const TransactionValidator = lazy(() => import('./components/TransactionValidator'))
const TemporalFilter = lazy(() => import('./components/TemporalFilter'))
const ReturnsCalculator = lazy(() => import('./components/ReturnsCalculator'))
const PerformanceDashboard = lazy(() => import('./components/PerformanceDashboard'))

const sections = {
  parser: TransactionParser,
  validator: TransactionValidator,
  filter: TemporalFilter,
  returns: ReturnsCalculator,
  performance: PerformanceDashboard,
}

function App() {
  const activeSection = useAppStore((s) => s.activeSection)
  const ActiveComponent = sections[activeSection]

  return (
    <div className="flex h-screen bg-gray-950">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e1e2e',
            color: '#e5e7eb',
            border: '1px solid #333',
          },
        }}
      />
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Suspense fallback={<LoadingSpinner />}>
          <ActiveComponent />
        </Suspense>
      </main>
    </div>
  )
}

export default App
