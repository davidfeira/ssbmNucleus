import { useState, useCallback } from 'react'

/**
 * Custom hook for managing modal state
 *
 * @param {any} initialData - Initial data for the modal (optional)
 * @returns {Object} Modal state and controls
 * @returns {boolean} isOpen - Whether the modal is open
 * @returns {any} data - Data passed to the modal
 * @returns {Function} open - Function to open modal with optional data
 * @returns {Function} close - Function to close modal and clear data
 * @returns {Function} setData - Function to update modal data while open
 */
export function useModalState(initialData = null) {
  const [isOpen, setIsOpen] = useState(false)
  const [data, setData] = useState(initialData)

  const open = useCallback((modalData = null) => {
    setData(modalData)
    setIsOpen(true)
  }, [])

  const close = useCallback(() => {
    setIsOpen(false)
    // Small delay before clearing data to allow for close animations
    setTimeout(() => setData(null), 300)
  }, [])

  const updateData = useCallback((newData) => {
    setData(newData)
  }, [])

  return {
    isOpen,
    data,
    open,
    close,
    setData: updateData
  }
}

/**
 * Custom hook for managing multiple related modals
 * Useful when you have several modals that should not be open simultaneously
 *
 * @param {string[]} modalNames - Array of modal names
 * @returns {Object} Modal state and controls
 */
export function useMultiModalState(modalNames) {
  const [activeModal, setActiveModal] = useState(null)
  const [modalData, setModalData] = useState({})

  const openModal = useCallback((modalName, data = null) => {
    if (!modalNames.includes(modalName)) {
      console.warn(`Modal "${modalName}" not found in modal names`)
      return
    }
    setActiveModal(modalName)
    setModalData(prev => ({ ...prev, [modalName]: data }))
  }, [modalNames])

  const closeModal = useCallback(() => {
    const currentModal = activeModal
    setActiveModal(null)
    // Clear data after close animation
    setTimeout(() => {
      setModalData(prev => ({ ...prev, [currentModal]: null }))
    }, 300)
  }, [activeModal])

  const updateModalData = useCallback((modalName, data) => {
    setModalData(prev => ({ ...prev, [modalName]: data }))
  }, [])

  // Generate helper objects for each modal
  const modals = {}
  modalNames.forEach(name => {
    modals[name] = {
      isOpen: activeModal === name,
      data: modalData[name] || null,
      open: (data) => openModal(name, data),
      close: closeModal,
      setData: (data) => updateModalData(name, data)
    }
  })

  return {
    activeModal,
    modals,
    openModal,
    closeModal,
    closeAll: closeModal
  }
}
