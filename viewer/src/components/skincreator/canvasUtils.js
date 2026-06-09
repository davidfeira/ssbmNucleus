// Pure canvas drawing helpers for the paint canvas (no React state)

export const getCanvasCoords = (canvas, e) => {
  if (!canvas) return null
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  return {
    x: Math.floor((e.clientX - rect.left) * scaleX),
    y: Math.floor((e.clientY - rect.top) * scaleY)
  }
}

export const drawBrush = (canvas, x, y, color, size) => {
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = color

  if (size === 1) {
    ctx.fillRect(x, y, 1, 1)
  } else {
    // Draw a square brush centered on the point
    const offset = Math.floor(size / 2)
    for (let dy = 0; dy < size; dy++) {
      for (let dx = 0; dx < size; dx++) {
        const px = x - offset + dx
        const py = y - offset + dy
        if (px >= 0 && px < canvas.width && py >= 0 && py < canvas.height) {
          ctx.fillRect(px, py, 1, 1)
        }
      }
    }
  }
}

export const eraseBrush = (canvas, x, y, size) => {
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  const offset = Math.floor(size / 2)
  for (let dy = 0; dy < size; dy++) {
    for (let dx = 0; dx < size; dx++) {
      const px = x - offset + dx
      const py = y - offset + dy
      if (px >= 0 && px < canvas.width && py >= 0 && py < canvas.height) {
        ctx.clearRect(px, py, 1, 1)
      }
    }
  }
}

export const drawLine = (x0, y0, x1, y1, toolFn) => {
  const dx = Math.abs(x1 - x0)
  const dy = Math.abs(y1 - y0)
  const sx = x0 < x1 ? 1 : -1
  const sy = y0 < y1 ? 1 : -1
  let err = dx - dy

  while (true) {
    toolFn(x0, y0)
    if (x0 === x1 && y0 === y1) break
    const e2 = 2 * err
    if (e2 > -dy) { err -= dy; x0 += sx }
    if (e2 < dx) { err += dx; y0 += sy }
  }
}

export const floodFill = (canvas, startX, startY, fillColor) => {
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  const data = imageData.data
  const width = canvas.width
  const height = canvas.height

  // Parse fill color
  const tempCanvas = document.createElement('canvas')
  tempCanvas.width = tempCanvas.height = 1
  const tempCtx = tempCanvas.getContext('2d')
  tempCtx.fillStyle = fillColor
  tempCtx.fillRect(0, 0, 1, 1)
  const fillRgba = tempCtx.getImageData(0, 0, 1, 1).data

  // Get target color
  const startIdx = (startY * width + startX) * 4
  const targetR = data[startIdx]
  const targetG = data[startIdx + 1]
  const targetB = data[startIdx + 2]
  const targetA = data[startIdx + 3]

  // Don't fill if same color
  if (targetR === fillRgba[0] && targetG === fillRgba[1] &&
      targetB === fillRgba[2] && targetA === fillRgba[3]) return

  const stack = [[startX, startY]]
  const visited = new Set()

  while (stack.length > 0) {
    const [x, y] = stack.pop()
    const key = `${x},${y}`

    if (visited.has(key)) continue
    if (x < 0 || x >= width || y < 0 || y >= height) continue

    const idx = (y * width + x) * 4
    if (data[idx] !== targetR || data[idx + 1] !== targetG ||
        data[idx + 2] !== targetB || data[idx + 3] !== targetA) continue

    visited.add(key)
    data[idx] = fillRgba[0]
    data[idx + 1] = fillRgba[1]
    data[idx + 2] = fillRgba[2]
    data[idx + 3] = fillRgba[3]

    stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1])
  }

  ctx.putImageData(imageData, 0, 0)
}
