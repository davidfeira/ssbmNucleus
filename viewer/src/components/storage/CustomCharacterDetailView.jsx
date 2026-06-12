import { useState, useEffect, useCallback, useRef } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import ConfirmDialog from '../shared/ConfirmDialog'
import InGameTestPanel from '../shared/InGameTestPanel'
import { useInGameTest } from '../../hooks/useInGameTest'
import { useEditModal } from '../../hooks/useEditModal'
import { useCspManager } from '../../hooks/useCspManager'
import EditModal from './EditModal'
import CspManagerModal from './CspManagerModal'
import PoseManagerModal from './PoseManagerModal'
import SoundBankModal from './SoundBankModal'
import EmbeddedModelViewer from '../EmbeddedModelViewer'
import SkinCreator from '../SkinCreator'

export default function CustomCharacterDetailView({ character, onBack, onDelete, onRename, API_URL }) {
  const [editingName, setEditingName] = useState(false)
  const [nameValue, setNameValue] = useState(character.name)
  const [saving, setSaving] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [detail, setDetail] = useState(null)
  const [seriesList, setSeriesList] = useState([])
  const [showSeriesPicker, setShowSeriesPicker] = useState(false)
  const [skinMessage, setSkinMessage] = useState('')
  const [importingSkin, setImportingSkin] = useState(false)
  const [seriesIconBust, setSeriesIconBust] = useState(0)
  const [assetBust, setAssetBust] = useState(0)
  const [draggingCostume, setDraggingCostume] = useState(null)  // bundled costume index being dragged
  const [skinDropActive, setSkinDropActive] = useState(false)
  const [renamingCostume, setRenamingCostume] = useState(null)  // { index, value }
  const [playingAudio, setPlayingAudio] = useState(null)        // 'victory' | 'announcer'
  const [skinCreatorCostume, setSkinCreatorCostume] = useState(null) // opens SkinCreator on this skin
  const [showPoseManager, setShowPoseManager] = useState(false)
  const [showSoundBank, setShowSoundBank] = useState(false)
  const [selectedTeamColor, setSelectedTeamColor] = useState(null)   // armed team token ('red'|'blue'|'green')
  const audioRef = useRef(null)
  const skinFileRef = useRef(null)
  const seriesFileRef = useRef(null)
  const iconFileRef = useRef(null)
  const bannerBigRef = useRef(null)
  const bannerSmallRef = useRef(null)
  const inGameTest = useInGameTest()

  const fetchDetail = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/detail`)
      const data = await response.json()
      if (data.success) setDetail(data.detail)
    } catch (err) {
      console.error('Failed to fetch character detail:', err)
    }
  }, [character.slug, API_URL])

  useEffect(() => { fetchDetail() }, [fetchDetail])

  // ── Shared skin-editing stack (same modal as canonical character skins).
  // Custom skins are exposed to it under a pseudo-character key whose
  // path maps straight to this character's skins directory.
  const pseudoCharacter = `custom_characters/${character.slug}/skins`
  const setEditingItemRef = useRef(null)

  const cspManager = useCspManager({
    API_URL,
    onRefresh: fetchDetail,
    onUpdateEditingItemAlts: (updater) => {
      setEditingItemRef.current?.(prev => prev ? {
        ...prev,
        data: {
          ...prev.data,
          alternateCsps: typeof updater === 'function'
            ? updater(prev.data.alternateCsps || [])
            : updater
        }
      } : prev)
    },
    onUpdateEditingItemActiveCsp: (activeCspId) => {
      setEditingItemRef.current?.(prev => prev ? {
        ...prev,
        data: { ...prev.data, active_csp_id: activeCspId }
      } : prev)
    },
    onUpdateEditingItemData: (updatedData) => {
      setEditingItemRef.current?.(prev => (
        prev?.type === 'costume' &&
        prev.data.id === updatedData.id &&
        prev.data.character === updatedData.character
          ? { ...prev, data: { ...prev.data, ...updatedData } }
          : prev
      ))
    }
  })

  const editModal = useEditModal({
    API_URL,
    onRefresh: fetchDetail,
    fetchStageVariants: async () => {},
    setLastImageUpdate: cspManager.setLastImageUpdate
  })
  setEditingItemRef.current = editModal.setEditingItem

  // Bundled costumes are mirrored by the backend into an editable library
  // under this second pseudo key (materialized zips, folded back at install)
  const pseudoCostumes = `custom_characters/${character.slug}/costumes`

  const openSkinEditorFor = (charKey, skin) => {
    const base = API_URL.replace('/api/mex', '')
    editModal.handleEditClick('costume', {
      id: skin.id,
      character: charKey,
      color: skin.name || skin.color,
      dat_name: skin.dat_name || skin.dat,
      has_csp: skin.has_csp,
      has_stock: skin.has_stock,
      cspUrl: `${base}/storage/${charKey}/${skin.csp_filename || `${skin.id}_csp.png`}`,
      hdCspUrl: skin.has_hd_csp
        ? `${base}/storage/${charKey}/${skin.hd_csp_filename || `${skin.id}_csp_hd.png`}`
        : null,
      stockUrl: skin.has_stock ? `${base}/storage/${charKey}/${skin.id}_stc.png` : null,
      slippi_safe: skin.slippi_safe,
      slippi_tested: skin.slippi_tested,
      slippi_manual_override: skin.slippi_manual_override,
      has_hd_csp: skin.has_hd_csp,
      hd_csp_resolution: skin.hd_csp_resolution,
      hd_csp_size: skin.hd_csp_size,
      active_csp_id: skin.active_csp_id || null,
      alternateCsps: (skin.alternate_csps || []).map(alt => ({
        id: alt.id,
        url: `/storage/${charKey}/${alt.filename}`,
        poseName: alt.pose_name,
        isHd: alt.is_hd,
        timestamp: alt.timestamp
      }))
    })
  }

  const openSkinEditor = (skin) => openSkinEditorFor(pseudoCharacter, skin)
  const openCostumeEditor = (costume) => {
    if (!costume.edit_id) return
    openSkinEditorFor(pseudoCostumes, { ...costume, id: costume.edit_id })
  }

  // Edit Textures: open the shared SkinCreator on this skin. Saving creates a
  // NEW entry in this character's Custom Skins (SkinCreator routes the save by
  // the pseudo-character key).
  const handleStartSkinCreator = (itemData) => {
    editModal.handleCancel()
    setSkinCreatorCostume({
      id: itemData.id,
      character: itemData.character,
      color: itemData.color,
      dat_name: itemData.dat_name,
    })
  }

  // Test in Game: build a temp ISO with this fighter + exactly this skin
  // (added skins are imported as an extra costume slot; bundled costumes are
  // selected by their slot index) and play a short match.
  const handleTestInGame = () => {
    const item = editModal.editingItem
    if (!item) return
    if (item.data.character?.endsWith('/costumes')) {
      const costume = (detail?.costumes || []).find(c => c.edit_id === item.data.id)
      inGameTest.startCustomCharacterSkinTest({
        slug: character.slug,
        costumeIndex: costume?.index ?? 0,
        colorName: item.data.color,
      })
    } else {
      inGameTest.startCustomCharacterSkinTest({
        slug: character.slug,
        skinId: item.data.id,
        colorName: item.data.color,
      })
    }
  }

  // The modal's Delete: a bundled costume must come out of fighter.zip via
  // the proper removal endpoint, not the skins-library delete
  const handleModalDelete = () => {
    const item = editModal.editingItem
    if (item?.data?.character?.endsWith('/costumes')) {
      const costume = (detail?.costumes || []).find(c => c.edit_id === item.data.id)
      if (!costume) return
      if (!window.confirm(`Remove costume "${costume.name}" from ${character.name}?`)) return
      fetch(`${API_URL}/custom-characters/${character.slug}/costumes/${costume.index}/remove`, { method: 'POST' })
        .then(r => r.json())
        .then(async (data) => {
          if (data.success) {
            playSound('boop')
            editModal.handleCancel()
            await fetchDetail()
          } else {
            alert(data.error || 'Remove failed')
          }
        })
        .catch(err => alert(`Remove error: ${err.message}`))
    } else {
      editModal.handleDelete()
    }
  }

  const handleSlippiRetest = async () => {
    const item = editModal.editingItem
    if (!item) return
    try {
      const response = await fetch(`${API_URL}/storage/costumes/retest-slippi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character: item.data.character, skinId: item.data.id })
      })
      const data = await response.json()
      if (data.success) {
        playSound('boop')
        editModal.setEditingItem(prev => prev ? {
          ...prev,
          data: { ...prev.data, slippi_safe: data.slippi_safe, slippi_tested: true, slippi_manual_override: null }
        } : prev)
        await fetchDetail()
      } else {
        alert(data.error || 'Retest failed')
      }
    } catch (err) {
      alert(`Retest error: ${err.message}`)
    }
  }

  const handleSlippiOverride = async (slippiSafe) => {
    const item = editModal.editingItem
    if (!item) return
    try {
      const response = await fetch(`${API_URL}/storage/costumes/override-slippi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character: item.data.character, skinId: item.data.id, slippiSafe })
      })
      const data = await response.json()
      if (data.success) {
        playSound('boop')
        editModal.setEditingItem(prev => prev ? {
          ...prev,
          data: { ...prev.data, slippi_safe: slippiSafe, slippi_manual_override: true }
        } : prev)
        await fetchDetail()
      } else {
        alert(data.error || 'Override failed')
      }
    } catch (err) {
      alert(`Override error: ${err.message}`)
    }
  }

  useEffect(() => {
    fetch(`${API_URL}/custom-characters/series-list`)
      .then(res => res.json())
      .then(data => { if (data.success) setSeriesList(data.series || []) })
      .catch(err => console.error('Failed to fetch series list:', err))
  }, [API_URL])

  const flashSkinMessage = (msg) => {
    setSkinMessage(msg)
    setTimeout(() => setSkinMessage(''), 4000)
  }

  const handleSaveRename = async () => {
    const trimmed = nameValue.trim()
    if (!trimmed || trimmed === character.name) {
      setEditingName(false)
      setNameValue(character.name)
      return
    }
    setSaving(true)
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ newName: trimmed })
      })
      const data = await response.json()
      if (data.success) {
        setEditingName(false)
        onRename({ ...character, name: trimmed })
      } else {
        alert(data.error || 'Rename failed')
      }
    } catch (err) {
      alert(`Rename error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/delete`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.success) {
        onDelete()
      } else {
        alert(data.error || 'Delete failed')
      }
    } catch (err) {
      alert(`Delete error: ${err.message}`)
    } finally {
      setDeleting(false)
      setShowConfirmDialog(false)
    }
  }

  const handleExport = () => {
    const link = document.createElement('a')
    link.href = `${API_URL}/custom-characters/${character.slug}/export`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleSetSeries = async (seriesId) => {
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/set-series`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seriesId })
      })
      const data = await response.json()
      if (data.success) {
        playSound('boop')
        setShowSeriesPicker(false)
        await fetchDetail()
      } else {
        alert(data.error || 'Failed to set franchise')
      }
    } catch (err) {
      alert(`Set franchise error: ${err.message}`)
    }
  }

  const handleActivateCustomSeries = async () => {
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/set-series-custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      const data = await response.json()
      if (data.success) {
        playSound('boop')
        setShowSeriesPicker(false)
        await fetchDetail()
      } else {
        alert(data.error || 'Failed to activate custom franchise')
      }
    } catch (err) {
      alert(`Custom franchise error: ${err.message}`)
    }
  }

  const handleRenameCustomSeries = async () => {
    const current = detail?.custom_series?.name || ''
    const name = window.prompt('Franchise name (used to share the series between characters):', current)
    if (!name || name.trim() === current) return
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/set-series-custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() })
      })
      const data = await response.json()
      if (data.success) {
        playSound('boop')
        await fetchDetail()
      } else {
        alert(data.error || 'Rename failed')
      }
    } catch (err) {
      alert(`Rename error: ${err.message}`)
    }
  }

  const handleUploadSeriesIcon = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/replace-series-icon`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        setShowSeriesPicker(false)
        setSeriesIconBust(Date.now())
        await fetchDetail()
      } else {
        alert(data.error || 'Icon upload failed')
      }
    } catch (err) {
      alert(`Icon upload error: ${err.message}`)
    }
  }

  // CSS icon + result banners — replaced inside fighter.zip so installs pick them up
  const handleReplaceAsset = async (which, e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/replace-asset/${which}`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        setAssetBust(Date.now())
        await fetchDetail()
      } else {
        alert(data.error || 'Replace failed')
      }
    } catch (err) {
      alert(`Replace error: ${err.message}`)
    }
  }

  const handleToggleWallJump = async () => {
    if (!detail) return
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/set-wall-jump`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ canWallJump: !detail.can_wall_jump })
      })
      const data = await response.json()
      if (data.success) {
        playSound('boop')
        await fetchDetail()
      } else {
        alert(data.error || 'Toggle failed')
      }
    } catch (err) {
      alert(`Toggle error: ${err.message}`)
    }
  }

  // Team color tokens: click a token to arm it, then click a costume card to
  // assign — same interaction as the install page's vanilla character panel.
  const handleTeamColorClick = (team) => {
    playSound('boop')
    setSelectedTeamColor(selectedTeamColor === team ? null : team)
  }

  const handleCostumeTeamAssign = async (index) => {
    if (!selectedTeamColor || !detail) return
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/set-team-colors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [selectedTeamColor]: index })
      })
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        setSelectedTeamColor(null)
        await fetchDetail()
      } else {
        alert(data.error || 'Set team color failed')
      }
    } catch (err) {
      alert(`Set team color error: ${err.message}`)
    }
  }

  const getCostumeTeamColors = (index) => {
    const tc = detail?.team_colors
    if (!tc) return []
    return ['red', 'blue', 'green'].filter(team => tc[team] === index)
  }

  const saveCostumeRename = async () => {
    const target = renamingCostume
    setRenamingCostume(null)
    if (!target) return
    const name = target.value.trim()
    if (!name) return
    try {
      const response = await fetch(
        `${API_URL}/custom-characters/${character.slug}/costumes/${target.index}/rename`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name })
        }
      )
      const data = await response.json()
      if (data.success) {
        playSound('boop')
        await fetchDetail()
      } else {
        alert(data.error || 'Rename failed')
      }
    } catch (err) {
      alert(`Rename error: ${err.message}`)
    }
  }

  const handleCostumeToSkin = async (index) => {
    setSkinDropActive(false)
    setDraggingCostume(null)
    if (index == null) return
    try {
      const response = await fetch(
        `${API_URL}/custom-characters/${character.slug}/costumes/${index}/to-skin`,
        { method: 'POST' }
      )
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        flashSkinMessage(`Moved ${data.skin.name} to custom skins`)
        await fetchDetail()
      } else {
        flashSkinMessage(`Move failed: ${data.error}`)
      }
    } catch (err) {
      flashSkinMessage(`Move error: ${err.message}`)
    }
  }

  const handleImportSkin = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setImportingSkin(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', file.name.replace(/\.[^.]+$/, ''))
    try {
      const response = await fetch(`${API_URL}/custom-characters/${character.slug}/skins/add`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        flashSkinMessage(`Added skin ${data.skin.name}`)
        await fetchDetail()
      } else {
        flashSkinMessage(`Add failed: ${data.error}`)
      }
    } catch (err) {
      flashSkinMessage(`Add error: ${err.message}`)
    } finally {
      setImportingSkin(false)
    }
  }

  // stop audio when leaving the page
  useEffect(() => () => { audioRef.current?.pause() }, [])

  const toggleAudio = (kind) => {
    if (playingAudio === kind) {
      audioRef.current?.pause()
      audioRef.current = null
      setPlayingAudio(null)
      return
    }
    audioRef.current?.pause()
    const path = kind === 'victory' ? 'victory-theme' : 'announcer'
    const audio = new Audio(`${API_URL}/custom-characters/${character.slug}/audio/${path}`)
    audio.onended = () => setPlayingAudio(null)
    audio.onerror = () => setPlayingAudio(null)
    audioRef.current = audio
    audio.play().catch(() => setPlayingAudio(null))
    setPlayingAudio(kind)
  }

  const hasIcon = detail ? detail.has_css_icon : character.has_css_icon
  const iconUrl = hasIcon
    ? `${API_URL}/custom-characters/${character.slug}/icon${assetBust ? `?v=${assetBust}` : ''}`
    : null

  const costumes = detail?.costumes || []
  const addedSkins = detail?.added_skins || []
  const BACKEND_BASE = API_URL.replace('/api/mex', '')
  const bigBanner = detail?.zip_assets?.big_banner
  const smallBanner = detail?.zip_assets?.small_banner

  const customSeriesActive = detail?.custom_series?.active

  // Editable controls (toggles, audio, replaceable assets)
  const editCells = detail ? [
    {
      label: 'Wall Jump',
      content: (
        <button
          className={`char-info-toggle ${detail.can_wall_jump ? 'on' : ''}`}
          onMouseEnter={playHoverSound}
          onClick={handleToggleWallJump}
          title="Toggle whether this character can wall jump"
        >
          {detail.can_wall_jump ? 'Yes' : 'No'}
        </button>
      )
    },
    detail.victory_theme_info?.available && {
      label: 'Victory Theme',
      content: (
        <span className="char-audio-row" title="Ported into your project on install">
          <button
            className={`char-audio-btn ${playingAudio === 'victory' ? 'playing' : ''}`}
            onMouseEnter={playHoverSound}
            onClick={() => toggleAudio('victory')}
          >
            {playingAudio === 'victory' ? '⏸' : '▶'}
          </button>
          <span className="char-audio-name" title={detail.victory_theme_info.name}>
            {detail.victory_theme_info.name}
          </span>
        </span>
      )
    },
    detail.announcer_available && {
      label: 'Announcer',
      content: (
        <span className="char-audio-row">
          <button
            className={`char-audio-btn ${playingAudio === 'announcer' ? 'playing' : ''}`}
            onMouseEnter={playHoverSound}
            onClick={() => toggleAudio('announcer')}
          >
            {playingAudio === 'announcer' ? '⏸' : '▶'}
          </button>
          <span className="char-audio-name">Play call</span>
        </span>
      )
    },
    detail.has_sound_pack && {
      label: 'Sound Bank',
      content: (
        <button
          className="char-info-toggle"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); setShowSoundBank(true) }}
          title="Browse, preview and replace this character's sounds"
        >
          🔊 Browse
        </button>
      )
    },
    smallBanner && {
      label: 'Small Banner',
      content: (
        <span
          className="char-info-banner"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); bannerSmallRef.current?.click() }}
          title="Small result banner (120x24) — click to replace"
        >
          <img
            src={`${BACKEND_BASE}${smallBanner.url}${assetBust ? `?v=${assetBust}` : ''}`}
            alt="small banner"
          />
        </span>
      )
    },
  ].filter(Boolean) : []

  // Read-only facts (compact strip)
  const infoPairs = detail ? [
    ['Source', character.source === 'zip' ? 'Imported ZIP' : 'ISO Scan'],
    ['Added', new Date(character.date_added).toLocaleDateString()],
    detail.based_on && ['Based On', detail.based_on],
    ['Costumes', `${costumes.length}${addedSkins.length ? ` + ${addedSkins.length} custom` : ''}`],
    detail.anim_count != null && ['Animations', detail.anim_count],
    detail.sound_bank != null && ['Sound Bank', detail.has_sound_pack ? `${detail.sound_bank} (custom)` : detail.sound_bank],
    !detail.victory_theme_info?.available && detail.victory_theme != null && ['Victory Theme', `#${detail.victory_theme}`],
    !detail.announcer_available && detail.announcer_call != null && ['Announcer Call', `#${detail.announcer_call}`],
    ['Kirby Cap', detail.has_kirby_cap ? 'Yes' : 'No'],
    detail.ending_movies > 0 && ['Ending Movies', detail.ending_movies],
    detail.files?.fighterDataPath && ['Fighter File', detail.files.fighterDataPath],
  ].filter(Boolean) : []

  const testActive = inGameTest.testingInGame || inGameTest.testResult || inGameTest.testError

  return (
    <div className="storage-viewer">
      <div className="character-detail">
        {/* ── Top bar: back + test CTA ── */}
        <div className="detail-top-bar">
          <button
            onClick={() => { playSound('back'); onBack(); }}
            className="back-button"
          >
            ← Back to Custom Characters
          </button>
          {!testActive && (
            <button
              className="ingame-test-cta"
              onMouseEnter={playHoverSound}
              onClick={() => {
                playSound('start')
                inGameTest.startCustomCharacterTest({ slug: character.slug, name: character.name })
              }}
              title="Build a one-mod test ISO and play a short match to verify it loads"
            >
              🎮 Test in Game
            </button>
          )}
        </div>

        {testActive && (
          <div className="ingame-test-stage">
            <InGameTestPanel
              test={inGameTest}
              onStart={() => inGameTest.startCustomCharacterTest({ slug: character.slug, name: character.name })}
            />
          </div>
        )}

        {/* ── Header: editable icon + name + franchise + result banner ── */}
        <div className="custom-char-header">
          <div
            className="custom-char-icon-wrap"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); iconFileRef.current?.click() }}
            title="Replace CSS icon (64x56)"
          >
            {iconUrl ? (
              <img src={iconUrl} alt={`${character.name} icon`} className="custom-char-icon" />
            ) : (
              <span className="custom-char-icon-placeholder">{(character.name || '?')[0]}</span>
            )}
            <span className="custom-char-icon-edit">✎</span>
          </div>
          <input
            ref={iconFileRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => handleReplaceAsset('icon', e)}
            style={{ display: 'none' }}
          />

          <div className="custom-char-title">
            {editingName ? (
              <div className="custom-char-name-edit">
                <input
                  type="text"
                  value={nameValue}
                  onChange={(e) => setNameValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveRename()
                    if (e.key === 'Escape') { setEditingName(false); setNameValue(character.name) }
                  }}
                  autoFocus
                  className="edit-name-input"
                  disabled={saving}
                />
                <button className="mode-btn" onClick={handleSaveRename} disabled={saving}>
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button className="mode-btn" onClick={() => { setEditingName(false); setNameValue(character.name) }}>
                  Cancel
                </button>
              </div>
            ) : (
              <h2 className="custom-char-name">
                {character.name}
                <button
                  className="series-change-btn"
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('boop'); setEditingName(true) }}
                  title="Rename character"
                >
                  ✎
                </button>
              </h2>
            )}

            {detail?.series_id != null && (
              <div className="custom-char-franchise">
                {customSeriesActive ? (
                  <>
                    {detail.custom_series.icon_url && (
                      <img
                        src={`${BACKEND_BASE}${detail.custom_series.icon_url}?v=${seriesIconBust}`}
                        alt=""
                        className="series-emblem"
                      />
                    )}
                    <span>{detail.custom_series.name || `Custom series ${detail.custom_series.source_id ?? ''}`}</span>
                    <button
                      className="series-change-btn"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('boop'); handleRenameCustomSeries() }}
                      title="Rename custom franchise"
                    >
                      ✏ name
                    </button>
                  </>
                ) : (
                  <>
                    {detail.series_icon_url && (
                      <img
                        src={`${BACKEND_BASE}${detail.series_icon_url}`}
                        alt=""
                        className="series-emblem"
                      />
                    )}
                    <span>{detail.series_name || `Series ${detail.series_id} (custom, not extracted)`}</span>
                  </>
                )}
                <button
                  className="series-change-btn"
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('boop'); setShowSeriesPicker(!showSeriesPicker) }}
                  title="Change franchise"
                >
                  ✎
                </button>
              </div>
            )}

            {character.has_fsm && (
              <div
                className="custom-char-fsm-badge"
                title="This character ships Frame Speed Modifier data (fsm.txt) — custom move speeds are baked into the game when you build an ISO"
              >
                ⚡ FSM move speeds
              </div>
            )}
          </div>

          {bigBanner && (
            <div
              className="custom-char-banner-wrap"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); bannerBigRef.current?.click() }}
              title="Result-screen banner (256x28) — click to replace"
            >
              <img
                src={`${BACKEND_BASE}${bigBanner.url}${assetBust ? `?v=${assetBust}` : ''}`}
                alt="result banner"
                className="custom-char-banner-img"
              />
              <span className="custom-char-icon-edit">✎</span>
            </div>
          )}
          <input
            ref={bannerBigRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => handleReplaceAsset('big_banner', e)}
            style={{ display: 'none' }}
          />
        </div>

        {showSeriesPicker && (
          <div className="series-picker">
            {detail?.custom_series && (
              <button
                className={`series-pick series-pick--custom ${customSeriesActive ? 'active' : ''}`}
                onMouseEnter={playHoverSound}
                onClick={handleActivateCustomSeries}
                title="Use this character's own franchise (added to your project on install)"
              >
                {detail.custom_series.icon_url ? (
                  <img src={`${BACKEND_BASE}${detail.custom_series.icon_url}?v=${seriesIconBust}`} alt="" />
                ) : (
                  <span className="series-pick-noicon">★</span>
                )}
                <span className="series-pick-name">{detail.custom_series.name || 'Custom'}</span>
              </button>
            )}
            {seriesList.map((s) => (
              <button
                key={s.id}
                className={`series-pick ${!customSeriesActive && s.id === detail?.series_id ? 'active' : ''}`}
                onMouseEnter={playHoverSound}
                onClick={() => handleSetSeries(s.id)}
                title={s.name}
              >
                {s.icon_url ? (
                  <img src={`${BACKEND_BASE}${s.icon_url}`} alt={s.name} />
                ) : (
                  <span className="series-pick-noicon">?</span>
                )}
                <span className="series-pick-name">{s.name}</span>
              </button>
            ))}
            <button
              className="series-pick series-pick--upload"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); seriesFileRef.current?.click() }}
              title="Upload your own franchise icon (PNG, shown at 80x64)"
            >
              <span className="series-pick-noicon">⬆</span>
              <span className="series-pick-name">Upload PNG…</span>
            </button>
            <input
              ref={seriesFileRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={handleUploadSeriesIcon}
              style={{ display: 'none' }}
            />
          </div>
        )}

        {/* ── Editable controls ── */}
        {detail && editCells.length > 0 && (
          <div className="char-edit-grid">
            {editCells.map((cell) => (
              <div key={cell.label} className="char-info-cell">
                <span className="char-info-label">{cell.label}</span>
                <span className="char-info-value">{cell.content}</span>
              </div>
            ))}
            <input
              ref={bannerSmallRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(e) => handleReplaceAsset('small_banner', e)}
              style={{ display: 'none' }}
            />
          </div>
        )}

        {/* ── Read-only info strip ── */}
        {detail && (
          <div className="char-info-strip">
            {infoPairs.map(([label, value]) => (
              <span key={label} className="char-info-pair">
                <span className="char-strip-label">{label}</span>
                <span className="char-strip-value">{value}</span>
              </span>
            ))}
          </div>
        )}

        {/* ── Costumes ── */}
        {costumes.length > 0 && (
          <div className="custom-char-costumes">
            <div className="custom-char-section-header">
              <h3 className="custom-char-section-title">Costumes</h3>
              {detail?.team_colors && costumes.length > 1 && (
                <div className="team-color-tokens">
                  {[
                    { id: 'red', label: 'R', color: '#ff4757' },
                    { id: 'blue', label: 'B', color: '#3742fa' },
                    { id: 'green', label: 'G', color: '#2ed573' }
                  ].map(c => (
                    <div
                      key={c.id}
                      className={`team-color-token ${selectedTeamColor === c.id ? 'selected' : ''}`}
                      style={{ '--token-color': c.color }}
                      onClick={() => handleTeamColorClick(c.id)}
                      onMouseEnter={playHoverSound}
                      title={`${c.id.charAt(0).toUpperCase() + c.id.slice(1)} Team - click to assign`}
                    >
                      {c.label}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="custom-char-costume-grid">
              {costumes.map((costume) => (
                <div
                  key={costume.index}
                  className={`custom-char-costume-card${draggingCostume === costume.index ? ' dragging' : ''}${selectedTeamColor ? ' team-assignable' : ''}`}
                  draggable={costumes.length > 1 && renamingCostume?.index !== costume.index && !selectedTeamColor}
                  onClick={selectedTeamColor ? () => handleCostumeTeamAssign(costume.index) : undefined}
                  onDragStart={(e) => {
                    e.dataTransfer.effectAllowed = 'move'
                    setDraggingCostume(costume.index)
                  }}
                  onDragEnd={() => { setDraggingCostume(null); setSkinDropActive(false) }}
                  title={selectedTeamColor
                    ? `Set as the ${selectedTeamColor} team costume`
                    : costumes.length > 1 ? 'Drag down into Custom Skins to make this a removable skin' : undefined}
                >
                  {costume.csp_url ? (
                    <img
                      src={`${costume.csp_url}?t=${cspManager.lastImageUpdate}`}
                      alt={costume.name}
                      className="custom-char-csp"
                    />
                  ) : (
                    <div className="custom-char-csp-placeholder">
                      {costume.name[0]}
                    </div>
                  )}
                  {costume.edit_id && (
                    <button
                      className="costume-edit-btn"
                      onMouseEnter={playHoverSound}
                      onClick={(e) => { e.stopPropagation(); playSound('boop'); openCostumeEditor(costume) }}
                      title="Edit costume"
                    >
                      ✎
                    </button>
                  )}
                  {costumes.length > 1 && getCostumeTeamColors(costume.index).length > 0 && (
                    <div className="team-color-badges">
                      {getCostumeTeamColors(costume.index).map(team => (
                        <div
                          key={team}
                          className={`team-color-badge team-${team}`}
                          title={`${team.charAt(0).toUpperCase() + team.slice(1)} Team`}
                        >
                          {team[0].toUpperCase()}
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="custom-char-costume-info">
                    {costume.stock_url && (
                      <img
                        src={costume.stock_url}
                        alt="stock"
                        className="custom-char-stock"
                      />
                    )}
                    {renamingCostume?.index === costume.index ? (
                      <input
                        className="costume-name-input"
                        value={renamingCostume.value}
                        onChange={(e) => setRenamingCostume({ index: costume.index, value: e.target.value })}
                        onBlur={saveCostumeRename}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') saveCostumeRename()
                          if (e.key === 'Escape') setRenamingCostume(null)
                        }}
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <span
                        className="custom-char-costume-name editable"
                        title={`${costume.dat || ''} — click to rename`}
                        onClick={() => {
                          if (selectedTeamColor) return  // card click assigns the team instead
                          playSound('boop'); setRenamingCostume({ index: costume.index, value: costume.name })
                        }}
                      >
                        {costume.name}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Custom skins (drop zone for bundled costumes) ── */}
        <div
          className={`custom-char-costumes custom-skin-dropzone${draggingCostume != null ? ' drop-ready' : ''}${skinDropActive ? ' drop-active' : ''}`}
          onDragOver={(e) => {
            if (draggingCostume != null) { e.preventDefault(); e.dataTransfer.dropEffect = 'move' }
          }}
          onDragEnter={(e) => {
            if (draggingCostume != null) { e.preventDefault(); setSkinDropActive(true) }
          }}
          onDragLeave={(e) => {
            if (e.currentTarget.contains(e.relatedTarget)) return
            setSkinDropActive(false)
          }}
          onDrop={(e) => { e.preventDefault(); handleCostumeToSkin(draggingCostume) }}
        >
          <h3 className="custom-char-section-title">Custom Skins</h3>
          {addedSkins.length === 0 && (
            <p className="custom-char-section-hint">
              Add extra skins for this character — import a costume zip/dat, drag a
              costume from above down here to make it removable, or drag a skin from
              a vanilla character&apos;s page onto this character.
            </p>
          )}
          <div className="custom-char-costume-grid">
            {addedSkins.map((skin) => (
              <div key={skin.id} className="custom-char-costume-card">
                {skin.csp_url ? (
                  <img
                    src={`${BACKEND_BASE}${skin.csp_url}?t=${cspManager.lastImageUpdate}`}
                    alt={skin.name}
                    className="custom-char-csp"
                  />
                ) : (
                  <div className="custom-char-csp-placeholder">
                    {(skin.name || '?')[0]}
                  </div>
                )}
                <button
                  className="costume-edit-btn"
                  onMouseEnter={playHoverSound}
                  onClick={(e) => { e.stopPropagation(); playSound('boop'); openSkinEditor(skin) }}
                  title="Edit skin"
                >
                  ✎
                </button>
                <div className="custom-char-costume-info">
                  {skin.stock_url && (
                    <img
                      src={`${BACKEND_BASE}${skin.stock_url}`}
                      alt="stock"
                      className="custom-char-stock"
                    />
                  )}
                  <span className="custom-char-costume-name" title={skin.name}>{skin.name}</span>
                </div>
              </div>
            ))}
            <div
              className="custom-char-costume-card custom-skin-add-card"
              onMouseEnter={playHoverSound}
              onClick={() => { if (!importingSkin) { playSound('boop'); skinFileRef.current?.click() } }}
              title="Import a costume .zip or .dat as a custom skin"
            >
              <div className="custom-char-csp-placeholder">+</div>
              <div className="custom-char-costume-info">
                <span className="custom-char-costume-name">
                  {importingSkin ? 'Importing...' : 'Add Skin'}
                </span>
              </div>
            </div>
          </div>
          <input
            ref={skinFileRef}
            type="file"
            accept=".zip,.dat,.usd"
            onChange={handleImportSkin}
            style={{ display: 'none' }}
          />
          {skinMessage && (
            <div className={`import-message ${skinMessage.includes('failed') || skinMessage.includes('error') ? 'error' : 'success'}`}>
              {skinMessage}
            </div>
          )}
        </div>

        <div className="custom-stage-actions">
          <button
            className="intake-import-btn"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); handleExport() }}
            disabled={character.source !== 'zip'}
            title={character.source !== 'zip' ? 'Export only available for ZIP imports' : 'Download original ZIP'}
          >
            Export ZIP
          </button>
          <button
            className="intake-import-btn"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); setShowConfirmDialog(true) }}
            style={{ background: 'var(--color-danger, #e53e3e)' }}
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>

      <ConfirmDialog
        show={showConfirmDialog}
        title="Delete Custom Character"
        message={`Are you sure you want to delete "${character.name}"? This cannot be undone.`}
        confirmText="Delete"
        onConfirm={handleDelete}
        onCancel={() => setShowConfirmDialog(false)}
      />

      {/* ── Shared skin editing stack (same modal as canonical skins) ── */}
      <EditModal
        show={editModal.showEditModal}
        editingItem={editModal.editingItem}
        editName={editModal.editName}
        onNameChange={editModal.setEditName}
        saving={editModal.saving}
        deleting={editModal.deleting}
        exporting={editModal.exporting}
        cspPreview={editModal.cspPreview}
        stockPreview={editModal.stockPreview}
        screenshotPreview={editModal.screenshotPreview}
        lastImageUpdate={cspManager.lastImageUpdate}
        editSlippiSafe={editModal.editSlippiSafe}
        onSlippiSafeChange={editModal.setEditSlippiSafe}
        slippiAdvancedOpen={editModal.slippiAdvancedOpen}
        onSlippiAdvancedToggle={() => editModal.setSlippiAdvancedOpen(!editModal.slippiAdvancedOpen)}
        onSave={editModal.handleSave}
        onCancel={() => { inGameTest.resetTest(); editModal.handleCancel(); }}
        onDelete={handleModalDelete}
        onExport={editModal.handleExport}
        onCspChange={editModal.handleCspChange}
        onStockChange={editModal.handleStockChange}
        onScreenshotChange={editModal.handleScreenshotChange}
        onSlippiRetest={handleSlippiRetest}
        onSlippiOverride={handleSlippiOverride}
        onOpenCspManager={cspManager.openCspManager}
        onOpenPoseManager={() => { playSound('boop'); setShowPoseManager(true); }}
        onStartSkinCreator={handleStartSkinCreator}
        onView3D={() => editModal.setShow3DViewer(true)}
        onTestInGame={handleTestInGame}
        testingInGame={inGameTest.testingInGame}
        testStatus={inGameTest.testStatus}
        testResult={inGameTest.testResult}
        testError={inGameTest.testError}
        testMode={inGameTest.testMode}
        onResetTest={inGameTest.resetTest}
        API_URL={API_URL}
      />
      <SkinCreator
        isOpen={skinCreatorCostume != null}
        onClose={() => setSkinCreatorCostume(null)}
        selectedCharacter={character.name}
        onRefresh={fetchDetail}
        initialCostume={skinCreatorCostume}
      />
      {editModal.show3DViewer && editModal.editingItem?.type === 'costume' && (
        <EmbeddedModelViewer
          character={editModal.editingItem.data.character}
          skinId={editModal.editingItem.data.id}
          onClose={() => editModal.setShow3DViewer(false)}
        />
      )}
      <CspManagerModal
        show={cspManager.showCspManager}
        cspManagerSkin={cspManager.cspManagerSkin}
        pendingMainCspPreview={cspManager.pendingMainCspPreview}
        hdCspInfo={cspManager.hdCspInfo}
        compareSliderPosition={cspManager.compareSliderPosition}
        lastImageUpdate={cspManager.lastImageUpdate}
        alternativeCsps={cspManager.alternativeCsps}
        capturingHdCsp={cspManager.capturingHdCsp}
        onClose={cspManager.closeCspManager}
        onCspManagerMainChange={cspManager.handleCspManagerMainChange}
        onCompareSliderStart={cspManager.handleCompareSliderStart}
        onSwapCsp={cspManager.handleSwapCsp}
        onRemoveAlternativeCsp={cspManager.handleRemoveAlternativeCsp}
        onAddAlternativeCsp={cspManager.handleAddAlternativeCsp}
        onCaptureHdCsp={cspManager.handleCaptureHdCsp}
        onRegenerateAltHd={cspManager.handleRegenerateAltHd}
        onResetToOriginal={cspManager.handleResetToOriginal}
        onOpenPoseManager={() => { playSound('boop'); setShowPoseManager(true); }}
        onSave={cspManager.handleSaveCspManager}
        onUploadMainCsp={cspManager.handleUploadMainCsp}
        onUploadAltCsp={cspManager.handleUploadAltCsp}
        API_URL={API_URL}
      />
      <PoseManagerModal
        show={showPoseManager}
        character={pseudoCostumes}
        displayName={character.name}
        baseSkinId={detail?.costumes?.[0]?.id}
        onClose={() => setShowPoseManager(false)}
        onRefresh={fetchDetail}
        API_URL={API_URL}
      />
      <SoundBankModal
        show={showSoundBank}
        slug={character.slug}
        displayName={character.name}
        onClose={() => { playSound('back'); setShowSoundBank(false) }}
        API_URL={API_URL}
      />
      <ConfirmDialog
        show={editModal.showConfirmDialog}
        title={editModal.confirmDialogData?.title}
        message={editModal.confirmDialogData?.message}
        confirmText={editModal.confirmDialogData?.confirmText}
        onConfirm={editModal.confirmDelete}
        onCancel={editModal.cancelDelete}
      />
    </div>
  )
}
