import { useState, useCallback } from 'react'

/**
 * Custom hook for handling API requests with loading and error states
 *
 * @returns {Object} API utilities
 * @returns {boolean} isLoading - Whether an API request is in progress
 * @returns {string|null} error - Error message if request failed
 * @returns {Function} request - Function to make API requests
 * @returns {Function} clearError - Function to clear error state
 */
export function useApi() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const request = useCallback(async (url, options = {}) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(url, options)

      // Check if response is ok
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`

        // Try to get error details from response body
        try {
          const data = await response.json()
          if (data.error) {
            errorMessage = data.error
          } else if (data.message) {
            errorMessage = data.message
          }
        } catch {
          // If response body isn't JSON, use status text
        }

        throw new Error(errorMessage)
      }

      // Parse response based on content type
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }

      return await response.text()
    } catch (err) {
      const errorMessage = err.message || 'An unknown error occurred'
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  return {
    isLoading,
    error,
    request,
    clearError
  }
}

/**
 * Custom hook for handling API requests with manual loading state control
 * Useful when you need more control over the loading state
 *
 * @returns {Object} API utilities
 * @returns {Function} request - Function to make API requests
 */
export function useApiRequest() {
  const request = useCallback(async (url, options = {}) => {
    try {
      const response = await fetch(url, options)

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`

        try {
          const data = await response.json()
          if (data.error) {
            errorMessage = data.error
          } else if (data.message) {
            errorMessage = data.message
          }
        } catch {
          // If response body isn't JSON, use status text
        }

        throw new Error(errorMessage)
      }

      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }

      return await response.text()
    } catch (err) {
      throw err
    }
  }, [])

  return { request }
}
