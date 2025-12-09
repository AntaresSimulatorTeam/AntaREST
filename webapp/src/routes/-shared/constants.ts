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

import SettingsBrightnessIcon from "@mui/icons-material/SettingsBrightness";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";

export const THEME_MODES = [
  {
    value: "system",
    icon: SettingsBrightnessIcon,
  },
  {
    value: "light",
    icon: LightModeIcon,
  },
  {
    value: "dark",
    icon: DarkModeIcon,
  },
] as const;

export const GITHUB_URL = "https://github.com/AntaresSimulatorTeam/AntaREST";
