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

import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import { Box, Typography } from "@mui/material";

interface Props {
  name: string;
}

function StudyOwnerTag({ name }: Props) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 0.25,
        color: "text.primary",
        bgcolor: "action.selected",
        px: 0.75,
        py: 0.125,
        borderRadius: 0.5,
        flexShrink: 0,
      }}
    >
      <PersonOutlineIcon sx={{ fontSize: 12 }} />
      <Typography variant="caption" sx={{ lineHeight: 1.6 }}>
        {name}
      </Typography>
    </Box>
  );
}

export default StudyOwnerTag;
