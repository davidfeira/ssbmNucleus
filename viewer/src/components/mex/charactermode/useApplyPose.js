/**
 * useApplyPose - "Pose" button on the install page (CostumesPanel).
 *
 * Opens the pose manager for the selected fighter; picking a pose applies it
 * to EVERY in-ISO costume: the backend matches each costume back to its
 * vault skin, reuses that skin's existing render of the pose, or renders it
 * now (saving it to the vault as an alternate CSP), then overwrites the
 * project portrait. A final recompile pass refreshes the .tex files the ISO
 * export reads.
 */
import { useState } from 'react'
import { playSound } from '../../../utils/sounds'

export default function useApplyPose({ API_URL, selectedFighter, refreshCostumes }) {
  const [showPoseModal, setShowPoseModal] = useState(false)
  // Vault character key for the modal/backend: the fighter name for
  // canonical characters, the custom-character pseudo key otherwise
  const [poseCharacter, setPoseCharacter] = useState(null)
  const [poseBaseSkinId, setPoseBaseSkinId] = useState(null)
  // The fighter the pose targets. Usually the selected fighter, but the
  // Zelda/Sheik split panel poses one half at a time, so it passes the
  // specific fighter to openPoseModal.
  const [poseFighter, setPoseFighter] = useState(null)
  const [pendingPose, setPendingPose] = useState(null)
  const [applying, setApplying] = useState(false)
  const [applyingPose, setApplyingPose] = useState(null)
  const [applyProgress, setApplyProgress] = useState({ current: 0, total: 0 })

  const openPoseModal = async (fighterArg) => {
    const fighter = fighterArg || selectedFighter
    if (!fighter) return
    let character = fighter.name
    let baseSkinId = null
    // Custom fighters keep their poses and skins under a pseudo vault key
    if (fighter.isMexFighter) {
      try {
        const res = await fetch(`${API_URL}/custom-characters/list`)
        const data = await res.json()
        const entry = (data.characters || []).find(c => c.name === fighter.name)
        if (entry) {
          character = `custom_characters/${entry.slug}/costumes`
          // The create-pose viewer needs a vault skin to load the model from
          const skinsRes = await fetch(
            `${API_URL}/storage/costumes?character=${encodeURIComponent(character)}`)
          const skinsData = await skinsRes.json()
          baseSkinId = skinsData.costumes?.[0]?.folder || null
        }
      } catch (err) {
        console.warn('Custom character lookup failed, using fighter name:', err)
      }
    }
    setPoseFighter(fighter)
    setPoseCharacter(character)
    setPoseBaseSkinId(baseSkinId)
    setShowPoseModal(true)
  }

  // Pose picked in the manager -> close it and ask for confirmation
  const handlePoseSelected = (pose) => {
    playSound('boop')
    setShowPoseModal(false)
    setPendingPose(pose)
  }

  const confirmApplyPose = async () => {
    const pose = pendingPose
    const fighter = poseFighter || selectedFighter
    setPendingPose(null)
    if (!pose || !fighter) return

    setApplying(true)
    setApplyingPose(pose)
    setApplyProgress({ current: 0, total: 0 })
    let applied = 0
    let generatedCount = 0
    let skipped = 0
    let failed = 0

    try {
      // 1. Match in-ISO costumes to vault skins
      const mapRes = await fetch(`${API_URL}/storage/poses/project-costume-map`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fighter: fighter.name,
          character: poseCharacter
        })
      })
      const mapData = await mapRes.json()
      if (!mapData.success) throw new Error(mapData.error || 'Failed to map costumes')

      const entries = mapData.costumes || []
      setApplyProgress({ current: 0, total: entries.length })

      // 2. Apply per costume (one request each so progress is real — a
      //    missing render takes seconds to generate)
      for (let i = 0; i < entries.length; i++) {
        const entry = entries[i]
        setApplyProgress({ current: i + 1, total: entries.length })
        if (!entry.skinId && !entry.vanillaCode) {
          console.warn(`No vault skin or vanilla costume matched for "${entry.name}" (${entry.fileName})`)
          skipped++
          continue
        }
        try {
          const res = await fetch(`${API_URL}/storage/poses/apply-to-costume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              character: entry.skinCharacter,
              skinId: entry.skinId,
              vanillaCode: entry.vanillaCode,
              poseName: pose.name,
              cspAsset: entry.cspAsset,
              fileName: entry.fileName
            })
          })
          const data = await res.json()
          if (data.success) {
            if (data.status === 'no_csp_asset') {
              skipped++
            } else {
              applied++
              if (data.generated) generatedCount++
            }
          } else {
            console.error(`Apply pose failed for "${entry.name}":`, data.error)
            failed++
          }
        } catch (err) {
          console.error(`Apply pose error for "${entry.name}":`, err)
          failed++
        }
      }

      // 3. Recompile the .tex files the ISO export actually reads
      if (applied > 0) {
        await fetch(`${API_URL}/storage/poses/apply-finish`, { method: 'POST' })
      }

      playSound(applied > 0 ? 'camera' : 'error')
      console.log(`✓ Pose "${pose.name}": ${applied} applied (${generatedCount} rendered), ${skipped} skipped, ${failed} failed`)
      if (skipped > 0 || failed > 0) {
        alert(`Pose applied to ${applied} costume(s).` +
          (skipped > 0 ? `\n${skipped} skipped (no matching vault skin).` : '') +
          (failed > 0 ? `\n${failed} failed — see console.` : ''))
      }

      await refreshCostumes(fighter.name)
    } catch (err) {
      console.error('Apply pose error:', err)
      playSound('error')
      alert(`Apply pose failed: ${err.message}`)
    } finally {
      setApplying(false)
      setApplyingPose(null)
    }
  }

  return {
    showPoseModal,
    setShowPoseModal,
    poseCharacter,
    poseBaseSkinId,
    poseFighter,
    pendingPose,
    setPendingPose,
    applying,
    applyingPose,
    applyProgress,
    openPoseModal,
    handlePoseSelected,
    confirmApplyPose
  }
}
