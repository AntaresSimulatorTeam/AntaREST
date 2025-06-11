import { app, BrowserWindow, ipcMain, Menu, MenuItemConstructorOptions } from "electron"
import path from "node:path"
import {openDialog} from "./dialog.js"


function createMenu(window: BrowserWindow) {
  const template: Array<MenuItemConstructorOptions> = [
    {
      label: 'File',
      submenu: [
        {
          label: "Open",
          click: (menuItem, window, event) => openDialog(window)
        },
        {role: 'quit'}
      ]
    },
  ]

  const menu = Menu.buildFromTemplate(template)
  window.setMenu(menu)
}

const createWindow = () => {
    const win = new BrowserWindow({
      webPreferences: {
        preload: path.join(app.getAppPath(), "dist-electron", "preload.cjs"),
      }
    })

    createMenu(win)

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
