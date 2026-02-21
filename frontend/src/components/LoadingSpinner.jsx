import React from 'react'

export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-4 border-gray-700 border-t-blue-500 animate-spin" />
        <p className="mt-4 text-gray-400 text-sm text-center">Loading...</p>
      </div>
    </div>
  )
}
