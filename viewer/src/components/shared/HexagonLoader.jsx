import './HexagonLoader.css'

const HEXAGON_POINTS = '50,2 91.7,26 91.7,74 50,98 8.3,74 8.3,26'

export default function HexagonLoader({
  size = 96,
  className = '',
  label = 'Loading',
  decorative = false
}) {
  const classes = ['hexagon-loader', className].filter(Boolean).join(' ')

  return (
    <div
      className={classes}
      style={{ '--hexagon-loader-size': `${size}px` }}
      role={decorative ? undefined : 'img'}
      aria-label={decorative ? undefined : label}
      aria-hidden={decorative || undefined}
    >
      <svg viewBox="-4 -4 108 108" focusable="false">
        <polygon className="hexagon-loader-border" points={HEXAGON_POINTS} />
        <polygon className="hexagon-loader-glow" points={HEXAGON_POINTS} />
      </svg>
    </div>
  )
}
