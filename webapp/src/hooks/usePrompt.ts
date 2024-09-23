/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import useBlocker from "./useBlocker";

// * Workaround until it will be supported by react-router v6.
// * Based on https://ui.dev/react-router-preventing-transitions

function usePrompt(message: string, when = true): void {
  useBlocker((tx) => {
    if (window.confirm(message)) {
      tx.retry();
    }
  }, when);
}

export default usePrompt;
