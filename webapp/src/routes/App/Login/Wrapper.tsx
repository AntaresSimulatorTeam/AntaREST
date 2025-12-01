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

import { Box, ToggleButton, ToggleButtonGroup, Tooltip, useColorScheme } from "@mui/material";
import { THEME_MODES } from "../shared/constants";
import { useTranslation } from "react-i18next";

interface Props {
  children: React.ReactNode;
}

function Wrapper({ children }: Props) {
  const { t } = useTranslation();
  const { mode, setMode } = useColorScheme();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleThemeModeChange = (
    event: React.MouseEvent<HTMLElement>,
    newMode: (typeof THEME_MODES)[number]["value"],
  ) => {
    setMode(newMode);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        height: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <ToggleButtonGroup
        sx={{
          position: "absolute",
          top: 10,
          right: 10,
        }}
        value={mode}
        exclusive
        onChange={handleThemeModeChange}
      >
        {THEME_MODES.map(({ value, icon: Icon }) => (
          <Tooltip key={value} title={t(`global.${value}`)}>
            <ToggleButton value={value}>
              <Icon />
            </ToggleButton>
          </Tooltip>
        ))}
      </ToggleButtonGroup>
      {children}
    </Box>
  );
}

export default Wrapper;
