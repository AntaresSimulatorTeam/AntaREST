import { app, BrowserWindow } from "electron"
import path from "node:path"


const createWindow = () => {
  const win = new BrowserWindow({
    webPreferences: {
      preload: path.join(app.getAppPath(), "dist-electron", "preload.cjs")
    }
  })

  win.loadURL('http://localhost:3000/index.html')
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
