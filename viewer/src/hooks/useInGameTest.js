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

  // Capture a clean in-game screenshot of a stage variant and save it as the
  // variant's preview. Reuses the same overlay state (testingInGame/testStatus/
  // testResult) but follows the capture_* socket events; on success testResult
  // carries the saved screenshot so the overlay shows it.
  const captureStageScreenshot = async ({ stageCode, stageFolder, variantId, name, button }) => {
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
    setTestStatus({ stage: 'starting', percentage: 0, message: 'Starting screenshot capture…' })
    setTestResult(null)
    setTestError(null)

    cleanupSocket()
    const socket = io(BACKEND_URL)
    socketRef.current = socket
    socket.on('capture_progress', (d) => setTestStatus(d))
    socket.on('capture_complete', (d) => {
      setTestingInGame(false)
      // The image is returned (not yet saved) -- the overlay asks the user
      // whether to replace the variant's current screenshot with this one.
      setTestResult({
        success: true,
        captured: true,
        reason: 'Replace this stage’s current screenshot with the captured shot?',
        screenshot: d.screenshot || null,
        stageFolder: d.stageFolder,
        variantId: d.variantId,
      })
      playSound('achievement')
      cleanupSocket()
    })
    socket.on('capture_error', (d) => {
      setTestingInGame(false)
      setTestError(d.error || 'Screenshot capture failed')
      playSound('error')
      cleanupSocket()
    })

    try {
      const response = await fetch(`${API_URL}/test-in-game/capture-stage-screenshot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stageCode, stageFolder, variantId, name, button, vanillaIsoPath, slippiDolphinPath })
      })
      const data = await response.json()
      if (!data.success) {
        setTestingInGame(false)
        setTestError(data.error || 'Failed to start capture')
        playSound('error')
        cleanupSocket()
      }
    } catch (err) {
      setTestingInGame(false)
      setTestError(`Failed to start capture: ${err.message}`)
      playSound('error')
      cleanupSocket()
    }
  }

  // Capture a LIVE pause-screen screenshot for a pause mod. The backend builds
  // a vanilla+mod ISO, pauses a solo match, grabs the overlay, and saves the
  // shot as the mod's preview before capture_complete arrives.
  const capturePauseScreenshot = async ({ modId, name }) => {
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
    setTestStatus({ stage: 'starting', percentage: 0, message: 'Starting pause screenshot capture…' })
    setTestResult(null)
    setTestError(null)

    cleanupSocket()
    const socket = io(BACKEND_URL)
    socketRef.current = socket
    socket.on('capture_progress', (d) => setTestStatus(d))
    socket.on('capture_complete', (d) => {
      setTestingInGame(false)
      setTestResult({
        success: true,
        captured: true,
        reason: `Saved as the preview for "${name || 'this mod'}".`,
        screenshot: d.screenshot || null,
        modId: d.modId,
      })
      playSound('achievement')
      cleanupSocket()
    })
    socket.on('capture_error', (d) => {
      setTestingInGame(false)
      setTestError(d.error || 'Screenshot capture failed')
      playSound('error')
      cleanupSocket()
    })

    try {
      const response = await fetch(`${API_URL}/test-in-game/capture-pause-screenshot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modId, vanillaIsoPath, slippiDolphinPath })
      })
      const data = await response.json()
      if (!data.success) {
        setTestingInGame(false)
        setTestError(data.error || 'Failed to start capture')
        playSound('error')
        cleanupSocket()
      }
    } catch (err) {
      setTestingInGame(false)
      setTestError(`Failed to start capture: ${err.message}`)
      playSound('error')
      cleanupSocket()
    }
  }

  return {
    testingInGame, testStatus, testResult, testError,
    startCostumeTest, startCustomCharacterTest, startCustomStageTest, startStageSkinTest,
    captureStageScreenshot, capturePauseScreenshot,
    resetTest
  }
}
