import { useState, useEffect, useCallback } from 'react'

/**
 * Custom hook for state that persists to localStorage
 * Works like useState but automatically saves to and loads from localStorage
 *
 * @param {string} key - localStorage key
 * @param {any} defaultValue - Default value if nothing is stored
 * @returns {[any, Function]} State value and setter function
 */
export function usePersistentState(key, defaultValue) {
  // Initialize state from localStorage or default value
  const [state, setState] = useState(() => {
    try {
      const stored = localStorage.getItem(key)
      if (stored !== null) {
        return JSON.parse(stored)
      }
    } catch (err) {
      console.warn(`Error reading localStorage key "${key}":`, err)
    }
    return defaultValue
  })

  // Update localStorage whenever state changes
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(state))
    } catch (err) {
      console.warn(`Error writing localStorage key "${key}":`, err)
    }
  }, [key, state])

  return [state, setState]
}

/**
 * Custom hook for string values that persist to localStorage
 * Simpler version that doesn't use JSON serialization
 *
 * @param {string} key - localStorage key
 * @param {string} defaultValue - Default value if nothing is stored
 * @returns {[string, Function]} State value and setter function
 */
export function usePersistentString(key, defaultValue = '') {
  const [state, setState] = useState(() => {
    try {
      const stored = localStorage.getItem(key)
      if (stored !== null) {
        return stored
      }
    } catch (err) {
      console.warn(`Error reading localStorage key "${key}":`, err)
    }
    return defaultValue
  })

  useEffect(() => {
    try {
      localStorage.setItem(key, state)
    } catch (err) {
      console.warn(`Error writing localStorage key "${key}":`, err)
    }
  }, [key, state])

  return [state, setState]
}

/**
 * Hook to manage localStorage values without React state
 * Useful for values that don't need to trigger re-renders
 *
 * @param {string} key - localStorage key
 * @returns {Object} localStorage utilities
 */
export function useLocalStorage(key) {
  const get = useCallback(() => {
    try {
      const stored = localStorage.getItem(key)
      if (stored !== null) {
        return JSON.parse(stored)
      }
    } catch (err) {
      console.warn(`Error reading localStorage key "${key}":`, err)
    }
    return null
  }, [key])

  const set = useCallback((value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (err) {
      console.warn(`Error writing localStorage key "${key}":`, err)
    }
  }, [key])

  const remove = useCallback(() => {
    try {
      localStorage.removeItem(key)
    } catch (err) {
      console.warn(`Error removing localStorage key "${key}":`, err)
    }
  }, [key])

  const getString = useCallback(() => {
    try {
      return localStorage.getItem(key)
    } catch (err) {
      console.warn(`Error reading localStorage key "${key}":`, err)
      return null
    }
  }, [key])

  const setString = useCallback((value) => {
    try {
      localStorage.setItem(key, value)
    } catch (err) {
      console.warn(`Error writing localStorage key "${key}":`, err)
    }
  }, [key])

  return {
    get,
    set,
    remove,
    getString,
    setString
  }
}
