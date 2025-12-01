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

import { initConfig } from "./services/config";
import { createRoot } from "react-dom/client";
import App from "./components/App";
import storage, { StorageKey } from "./services/utils/localStorage";

initConfig().then((config) => {
  const versionInstalled = storage.getItem(StorageKey.Version);
  storage.setItem(StorageKey.Version, config.versionInfo.gitcommit);
  if (versionInstalled !== config.versionInfo.gitcommit) {
    window.location.reload();
  }

  const container = document.getElementById("root");

  if (!container) {
    throw new Error("Root container not found");
  }

  createRoot(container).render(<App />);
});
