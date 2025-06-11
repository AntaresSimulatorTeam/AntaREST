// The preload file needs to be a CommonJS module
// This is the only place we need to use required instead of import syntax

const electron  = require("electron")

electron.contextBridge.exposeInMainWorld('versions', {
  node: () => process.versions.node,
  chrome: () => process.versions.chrome,
  electron: () => process.versions.electron
  // we can also expose variables, not just functions
})

electron.contextBridge.exposeInMainWorld('openDialog',
  () => electron.ipcRenderer.send("open-dialog")
)
