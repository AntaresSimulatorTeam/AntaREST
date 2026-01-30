/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import EditIcon from "@mui/icons-material/Edit";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import { Box } from "@mui/material";

function EditorIcon() {
  return (
    <Box
      sx={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        mr: 1,
      }}
    >
      <PersonOutlineIcon
        sx={{
          color: "text.secondary",
        }}
      />
      <EditIcon
        sx={{
          color: "text.secondary",
          fontSize: "small",
          position: "absolute",
          bottom: 0,
          left: 11,
        }}
      />
    </Box>
  );
}

export default EditorIcon;
