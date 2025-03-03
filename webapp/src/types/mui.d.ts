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

import "@mui/material";
// cf. https://mui.com/material-ui/customization/css-theme-variables/usage/#typescript
// eslint-disable-next-line @typescript-eslint/no-restricted-imports
import type {} from "@mui/material/themeCssVarsAugmentation";

declare module "@mui/material" {
  interface InputBasePropsSizeOverrides {
    "extra-small": true;
  }

  interface TextFieldPropsSizeOverrides {
    "extra-small": true;
  }

  interface ToggleButtonGroupPropsSizeOverrides {
    "extra-small": true;
  }

  interface ToggleButtonPropsSizeOverrides {
    "extra-small": true;
  }

  interface CheckboxPropsSizeOverrides {
    "extra-small": true;
  }

  interface SvgIconPropsSizeOverrides {
    "extra-small": true;
  }
}
