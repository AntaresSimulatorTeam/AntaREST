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

import { colors, type ColorSystemOptions } from "@mui/material";

const BG = "#141a26";

export default {
  palette: {
    background: {
      default: BG,
      paper: BG,
    },
    primary: {
      main: colors.amber[500],
    },
    secondary: {
      main: colors.lightBlue[500],
    },
  },
} satisfies ColorSystemOptions;
