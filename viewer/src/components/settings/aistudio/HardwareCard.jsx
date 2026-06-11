/**
 * HardwareCard - detected GPU + disk, so model spec badges have context.
 */
import { fmtBytes } from './useAiEngine'

export default function HardwareCard({ status }) {
  if (!status) return null
  const gpu = status.hardware?.gpu
  const disk = status.hardware?.diskFreeBytes

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">Your machine</div>
      {gpu ? (
        <div className="aistudio-hw-row">
          <span className="aistudio-hw-gpu">🖥 {gpu.name}</span>
          <span className="aistudio-hw-detail">
            {(gpu.vramMb / 1024).toFixed(0)} GB VRAM
          </span>
          <span className="aistudio-hw-detail">
            {fmtBytes(disk)} free disk
          </span>
        </div>
      ) : (
        <div className="aistudio-callout warning">
          No NVIDIA GPU detected — local models won't run well here.
          Use the API models with an OpenRouter key instead.
        </div>
      )}
    </div>
  )
}
