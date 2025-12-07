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

import theme from "@/theme";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import {
  CssBaseline,
  ThemeProvider as MuiThemeProvider,
  StyledEngineProvider,
} from "@mui/material";

function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <StyledEngineProvider injectFirst>
      <MuiThemeProvider theme={theme} defaultMode="dark" noSsr>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </StyledEngineProvider>
  );
}

export default ThemeProvider;
