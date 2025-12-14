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

import { createRoot } from "react-dom/client";
import App from "./App";
import { initConfig } from "./services/config";
import storage, { StorageKey } from "./services/utils/localStorage";

if (process.env.NODE_ENV === "development") {
  // Remove message from Emotion library about unsafe usage in SSR
  const originalError = console.error;
  console.error = (message, ...rest) => {
    if (
      typeof message === "string" &&
      message.includes("unsafe when doing server-side rendering")
    ) {
      return;
    }
    originalError(message, ...rest);
  };
}

initConfig().then((config) => {
  const versionInstalled = storage.getItem(StorageKey.Version);
  storage.setItem(StorageKey.Version, config.versionInfo.gitcommit);
  if (versionInstalled !== config.versionInfo.gitcommit) {
    window.location.reload();
  }

  const rootContainer = document.getElementById("root");

  if (!rootContainer) {
    throw new Error("Root container not found");
  }

  createRoot(rootContainer).render(<App />);
});
