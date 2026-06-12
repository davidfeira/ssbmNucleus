/**
 * Client-side audio conversion for uploads.
 *
 * MeleeMedia (the backend's audio library) only reads wav/brstm/dsp/hps, so
 * anything else the user drops (mp3, ogg, m4a, flac...) is decoded here with
 * WebAudio — Chromium ships every common codec — and re-uploaded as 16-bit
 * PCM WAV. Native Melee formats pass through untouched.
 */

const PASSTHROUGH_EXTS = new Set(['wav', 'brstm', 'dsp', 'hps', 'ssm'])

export function needsConversion(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  return !PASSTHROUGH_EXTS.has(ext)
}

/**
 * Returns a File ready for upload: the original for native formats, or a
 * decoded .wav for everything else. Throws if the browser can't decode it.
 */
export async function toUploadableAudio(file) {
  if (!needsConversion(file)) return file

  const ctx = new AudioContext()
  try {
    const buffer = await ctx.decodeAudioData(await file.arrayBuffer())
    const wav = audioBufferToWav(buffer)
    const stem = file.name.replace(/\.[^.]+$/, '')
    return new File([wav], `${stem}.wav`, { type: 'audio/wav' })
  } finally {
    ctx.close()
  }
}

/** Encode an AudioBuffer as a 16-bit PCM WAV Blob (max 2 channels). */
function audioBufferToWav(buffer) {
  const channels = Math.min(2, buffer.numberOfChannels)
  const sampleRate = buffer.sampleRate
  const frames = buffer.length
  const dataSize = frames * channels * 2
  const out = new DataView(new ArrayBuffer(44 + dataSize))

  const writeStr = (offset, s) => {
    for (let i = 0; i < s.length; i++) out.setUint8(offset + i, s.charCodeAt(i))
  }
  writeStr(0, 'RIFF')
  out.setUint32(4, 36 + dataSize, true)
  writeStr(8, 'WAVE')
  writeStr(12, 'fmt ')
  out.setUint32(16, 16, true)
  out.setUint16(20, 1, true)              // PCM
  out.setUint16(22, channels, true)
  out.setUint32(24, sampleRate, true)
  out.setUint32(28, sampleRate * channels * 2, true)
  out.setUint16(32, channels * 2, true)
  out.setUint16(34, 16, true)
  writeStr(36, 'data')
  out.setUint32(40, dataSize, true)

  const chanData = []
  for (let c = 0; c < channels; c++) chanData.push(buffer.getChannelData(c))
  let offset = 44
  for (let i = 0; i < frames; i++) {
    for (let c = 0; c < channels; c++) {
      const v = Math.max(-1, Math.min(1, chanData[c][i]))
      out.setInt16(offset, v < 0 ? v * 0x8000 : v * 0x7FFF, true)
      offset += 2
    }
  }
  return new Blob([out.buffer], { type: 'audio/wav' })
}
