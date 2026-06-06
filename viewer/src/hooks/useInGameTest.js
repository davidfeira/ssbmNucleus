/**
 * useInGameTest Hook
 *
 * Drives the per-mod "Test in game" flow from an edit modal / detail view. Builds
 * a minimal temp ISO (vanilla + just this mod) on the backend, boots it in a
 * throwaway Dolphin, selects/triggers the mod, plays a short match, and reports
 * PASS / CRASH with a screenshot -- streamed over a short-lived SocketIO socket.
 *
 * Reads the vanilla ISO + Slippi paths the app already stores in localStorage,
 * so each caller just supplies the mod's identifier. Supports costumes, custom
 * characters, custom stages, and stage skins (DAS variants).
 */

import { useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { API_URL, BACKEND_URL } from '../config'
import { playSound } from '../utils/sounds'

export function useInGameTest() {
  const [testingInGame, setTestingInGame] = useState(false)
  const [testStatus, setTestStatus] = useState(null)   // { stage, percentage, message }
  const [testResult, setTestResult] = useState(null)   // test_complete payload
  const [testError, setTestError] = useState(null)
  const socketRef = useRef(null)

  const cleanupSocket = () => {
    if (socketRef.current) {
      try { socketRef.current.disconnect() } catch (e) { /* ignore */ }
      socketRef.current = null
    }
  }

  const resetTest = () => {
    cleanupSocket()
    setTestingInGame(false)
    setTestStatus(null)
    setTestResult(null)
    setTestError(null)
  }

  // Generic: POST to <endpoint> with the mod identity + the stored paths, then
  // follow progress/result over a short-lived socket.
  const runTest = async (endpoint, body) => {
    const vanillaIsoPath = localStorage.getItem('vanilla_iso_path')
    const slippiDolphinPath = localStorage.getItem('slippi_dolphin_path')

    if (!vanillaIsoPath) {
      setTestError('No vanilla Melee ISO path set. Set it in Settings first.')
      return
    }
    if (!slippiDolphinPath) {
      setTestError('No Slippi Dolphin path set. Set it in Settings first.')
      return
    }

    playSound('start')
    setTestingInGame(true)
    setTestStatus({ stage: 'starting', percentage: 0, message: 'Starting in-game test…' })
    setTestResult(null)
    setTestError(null)

    cleanupSocket()
    const socket = io(BACKEND_URL)
    socketRef.current = socket
    socket.on('test_progress', (d) => setTestStatus(d))
    socket.on('test_complete', (d) => {
      setTestingInGame(false)
      setTestResult(d)
      playSound(d.success ? 'achievement' : 'error')
      cleanupSocket()
    })
    socket.on('test_error', (d) => {
      setTestingInGame(false)
      setTestError(d.error || 'Test failed')
      playSound('error')
      cleanupSocket()
    })

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...body, vanillaIsoPath, slippiDolphinPath })
      })
      const data = await response.json()
      if (!data.success) {
        setTestingInGame(false)
        setTestError(data.error || 'Failed to start test')
        playSound('error')
        cleanupSocket()
      }
    } catch (err) {
      setTestingInGame(false)
      setTestError(`Failed to start test: ${err.message}`)
      playSound('error')
      cleanupSocket()
    }
  }

  const startCostumeTest = ({ character, skinId, colorName }) =>
    runTest('/test-in-game/costume', { character, skinId, colorName })

  const startCustomCharacterTest = ({ slug, name }) =>
    runTest('/test-in-game/custom-character', { slug, name })

  const startCustomStageTest = ({ slug, name }) =>
    runTest('/test-in-game/custom-stage', { slug, name })

  const startStageSkinTest = ({ stageCode, stageFolder, variantId, name, button }) =>
    runTest('/test-in-game/stage-skin', { stageCode, stageFolder, variantId, name, button })

  return {
    testingInGame, testStatus, testResult, testError,
    startCostumeTest, startCustomCharacterTest, startCustomStageTest, startStageSkinTest,
    resetTest
  }
}
