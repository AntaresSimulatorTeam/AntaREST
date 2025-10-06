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

import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
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
          fontSize: "inherit",
        }}
      />
      <EditOutlinedIcon
        sx={{
          color: "text.secondary",
          fontSize: "inherit",
          position: "absolute",
          bottom: -2,
          left: 8,
        }}
      />
    </Box>
  );
}

export default EditorIcon;
