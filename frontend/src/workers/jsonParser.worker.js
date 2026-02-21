// Web Worker for offloading large JSON parsing to a separate thread
// Prevents UI freezing when parsing 10^6 transaction files
self.onmessage = function (e) {
  try {
    const parsed = JSON.parse(e.data)
    self.postMessage({ success: true, data: parsed })
  } catch (err) {
    self.postMessage({ success: false, error: err.message })
  }
}
