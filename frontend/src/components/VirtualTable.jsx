import React, { useCallback, useMemo } from 'react'
import { FixedSizeList as List } from 'react-window'

export default function VirtualTable({ data, columns, height = 400, itemSize = 44 }) {
  const Row = useCallback(
    ({ index, style }) => (
      <div
        style={style}
        className={`flex items-center border-b border-gray-800 ${
          index % 2 === 0 ? 'bg-gray-900/50' : 'bg-gray-950/50'
        }`}
      >
        {columns.map((col) => (
          <div
            key={col.key}
            className="flex-1 px-4 py-2 text-sm text-gray-300 truncate"
            style={col.width ? { flex: `0 0 ${col.width}` } : undefined}
          >
            {col.render ? col.render(data[index][col.key], data[index]) : data[index][col.key]}
          </div>
        ))}
      </div>
    ),
    [data, columns]
  )

  const headerRow = useMemo(
    () => (
      <div className="flex bg-gray-800/80 border-b border-gray-700 sticky top-0 z-10">
        {columns.map((col) => (
          <div
            key={col.key}
            className="flex-1 px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider"
            style={col.width ? { flex: `0 0 ${col.width}` } : undefined}
          >
            {col.label}
          </div>
        ))}
      </div>
    ),
    [columns]
  )

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No data to display
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-gray-800 overflow-hidden">
      {headerRow}
      <List height={height} itemCount={data.length} itemSize={itemSize} width="100%">
        {Row}
      </List>
      <div className="px-4 py-2 bg-gray-900/50 border-t border-gray-800 text-xs text-gray-500">
        {data.length.toLocaleString()} rows
      </div>
    </div>
  )
}
