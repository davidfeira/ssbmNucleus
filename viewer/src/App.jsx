import { useState, useEffect } from 'react'
import StorageViewer from './components/StorageViewer'
import './App.css'

function App() {
  const [metadata, setMetadata] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadMetadata()
  }, [])

  async function loadMetadata() {
    try {
      // Fetch metadata from the storage directory
      const response = await fetch('/storage/metadata.json')
      if (!response.ok) {
        throw new Error('Failed to load metadata')
      }
      const data = await response.json()
      setMetadata(data)
      setError(null)
    } catch (err) {
      console.error('Error loading metadata:', err)
      setError('Failed to load storage metadata. Make sure the storage folder exists.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
        <p>Loading storage...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="app-error">
        <h2>⚠️ Error</h2>
        <p>{error}</p>
        <button onClick={loadMetadata} className="retry-button">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎮 Melee Costume Storage</h1>
        <p className="subtitle">Browse and manage your character skin collection</p>
      </header>

      <StorageViewer metadata={metadata} />
    </div>
  )
}

export default App
