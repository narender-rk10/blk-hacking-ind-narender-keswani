import React, { useState, useCallback, useRef } from 'react'
import { Upload, Clipboard, AlertCircle } from 'lucide-react'
import { useDebounce } from '../hooks/useDebounce'

export default function JsonInput({ label, placeholder, onParsed, sampleData }) {
  const [rawText, setRawText] = useState('')
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)
  const debouncedText = useDebounce(rawText, 300)

  const parseJSON = useCallback(
    (text) => {
      try {
        const parsed = JSON.parse(text)
        setError(null)
        onParsed(parsed)
      } catch (e) {
        setError(e.message)
      }
    },
    [onParsed]
  )

  // Web Worker for large files
  const parseWithWorker = useCallback(
    (text) => {
      if (text.length > 100000) {
        const worker = new Worker(
          new URL('../workers/jsonParser.worker.js', import.meta.url)
        )
        worker.onmessage = (e) => {
          worker.terminate()
          if (e.data.success) {
            setError(null)
            onParsed(e.data.data)
          } else {
            setError(e.data.error)
          }
        }
        worker.postMessage(text)
      } else {
        parseJSON(text)
      }
    },
    [onParsed, parseJSON]
  )

  const handleChange = useCallback(
    (e) => {
      const val = e.target.value
      setRawText(val)
    },
    []
  )

  const handleParse = useCallback(() => {
    if (rawText.trim()) {
      parseWithWorker(rawText)
    }
  }, [rawText, parseWithWorker])

  const handleFileUpload = useCallback(
    (e) => {
      const file = e.target.files[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = (event) => {
        const text = event.target.result
        setRawText(text)
        parseWithWorker(text)
      }
      reader.readAsText(file)
    },
    [parseWithWorker]
  )

  const handlePaste = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText()
      setRawText(text)
      parseWithWorker(text)
    } catch {
      setError('Could not read clipboard')
    }
  }, [parseWithWorker])

  const handleLoadSample = useCallback(() => {
    if (sampleData) {
      const text = JSON.stringify(sampleData, null, 2)
      setRawText(text)
      onParsed(sampleData)
      setError(null)
    }
  }, [sampleData, onParsed])

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-300">{label}</label>
        <div className="flex gap-2">
          {sampleData && (
            <button
              onClick={handleLoadSample}
              className="text-xs px-3 py-1.5 rounded bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 transition"
            >
              Load Sample
            </button>
          )}
          <button
            onClick={handlePaste}
            className="text-xs px-3 py-1.5 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 transition flex items-center gap-1"
          >
            <Clipboard size={12} /> Paste
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-xs px-3 py-1.5 rounded bg-gray-800 text-gray-400 hover:bg-gray-700 transition flex items-center gap-1"
          >
            <Upload size={12} /> Upload
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>
      </div>
      <textarea
        value={rawText}
        onChange={handleChange}
        placeholder={placeholder || 'Paste JSON here...'}
        className="json-input w-full h-48 bg-gray-900 border border-gray-700 rounded-lg p-4 text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-y"
        spellCheck="false"
      />
      {error && (
        <div className="flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle size={14} />
          {error}
        </div>
      )}
      <button
        onClick={handleParse}
        className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition"
      >
        Parse JSON
      </button>
    </div>
  )
}
