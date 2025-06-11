import {BaseWindow, BrowserWindow, dialog} from "electron"

export function openDialog(window: BaseWindow | undefined) {
    if (window) {
        dialog.showOpenDialog(window, {properties: ["openDirectory"]})
    }
}