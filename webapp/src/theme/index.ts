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

import { createTheme } from "@mui/material";
import components from "./components";
import colorSchemes from "./colorSchemes";

const theme = createTheme({
  // Enable CSS variables to use `colorSchemes.[mode].overlays` and access MUI variables dynamically.
  // In vanilla CSS, use `var(--mui-XXX)`.
  // In the MUI context, use `theme.vars.XXX`.
  cssVariables: {
    // Add the current color scheme name in the `class` attribute of the <html> element.
    // Useful for customizing third-party libraries.
    // Must be set to allow switching between modes when `cssVariables` is activated.
    colorSchemeSelector: "class",
  },
  colorSchemes,
  components,
});

export default theme;
