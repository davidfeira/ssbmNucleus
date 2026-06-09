// Helpers for exporting the DAT file from the embedded viewer via Electron IPC

// Request a DAT export from the viewer. The 'exportDat' viewer message resolves/rejects
// the promise through the resolver ref (handled by the viewer message handler).
export const requestExportDat = (exportDatResolverRef) => {
  return new Promise((resolve, reject) => {
    exportDatResolverRef.current = { resolve, reject }
    window.electron.viewerSend({ type: 'exportDat' })

    setTimeout(() => {
      if (exportDatResolverRef.current) {
        exportDatResolverRef.current = null
        reject(new Error('Export timed out'))
      }
    }, 30000)
  })
}

export const base64ToBlob = (base64Data) => {
  const byteCharacters = atob(base64Data)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  return new Blob([byteArray], { type: 'application/octet-stream' })
}
