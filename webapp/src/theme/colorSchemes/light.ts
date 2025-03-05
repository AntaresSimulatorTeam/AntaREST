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

import { colors, getOverlayAlpha, type ColorSystemOptions, type Overlays } from "@mui/material";

export default {
  palette: {
    primary: {
      main: colors.blue[600],
    },
    secondary: {
      main: colors.blueGrey[600],
    },
  },
  // Generates CSS variables for `Paper` elevation overlays (--mui-overlays-[0-24])
  overlays: Array.from({ length: 25 }, (_, i) => {
    if (i === 0) {
      return "none";
    }

    // Limit the alpha overlay to elevation level 3 because above that it's too dark
    const elevation = Math.min(i, 3);
    const alpha = getOverlayAlpha(elevation) + (elevation === 1 ? 0 : 0.01 * elevation);

    return `linear-gradient(rgba(0 0 0 / ${alpha}), rgba(0 0 0 / ${alpha}))`;
  }) as Overlays,
} satisfies ColorSystemOptions;
