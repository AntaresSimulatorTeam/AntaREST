/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { app, BrowserWindow, dialog, Menu, MenuItemConstructorOptions } from "electron";
import path from "node:path";
import { isDev } from "./utils.js";

function createMenu(window: BrowserWindow) {
  const devRoles: MenuItemConstructorOptions[] = [{ role: "toggleDevTools" }];
  const template: MenuItemConstructorOptions[] = [
    {
      label: "File",
      submenu: [
        {
          label: "Open",
          click: (menuItem, _, event) => {
            dialog.showOpenDialog(window, { properties: ["openDirectory"] }).then((ret) => {
              const path = ret.filePaths[0];
              console.log(`Got path ${path}`);
              window.webContents.send("open-study", path);
            });
          },
        },
        { role: "quit" },
      ],
    },
    ...(isDev() ? devRoles : []),
  ];

  const menu = Menu.buildFromTemplate(template);
  window.setMenu(menu);
}

const createWindow = () => {
  const win = new BrowserWindow({
    webPreferences: {
      preload: path.join(app.getAppPath(), "dist-electron", "preload.cjs"),
    },
  });

  createMenu(win);

  win.loadURL("http://localhost:3000/index.html");
};

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
