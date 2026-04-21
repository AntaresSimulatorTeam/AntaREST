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

import { buildModificationDate, convertUTCToLocalTime } from "@/services/utils";
import { compactSemanticVersion } from "@/utils/versionUtils";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import { Box, Divider, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

interface Props {
  creationDate: string;
  modificationDate: string;
  version: string;
  /** Pass true in grid mode where text must not wrap to a second line. */
  noWrap?: boolean;
}

function StudyMetadataRow({ creationDate, modificationDate, version, noWrap }: Props) {
  const { t, i18n } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center", flexShrink: 0 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.25 }}>
        <ScheduleOutlinedIcon sx={{ fontSize: 13, flexShrink: 0 }} />
        <Typography variant="caption" noWrap={noWrap}>
          {convertUTCToLocalTime(creationDate)}
        </Typography>
      </Box>
      <Divider orientation="vertical" flexItem sx={{ mx: 0.75 }} />
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.25 }}>
        <UpdateOutlinedIcon sx={{ fontSize: 13, color: "text.primary", flexShrink: 0 }} />
        <Typography variant="caption" noWrap={noWrap}>
          {buildModificationDate(modificationDate, t, i18n.language)}
        </Typography>
      </Box>
      <Divider orientation="vertical" flexItem sx={{ mx: 0.75 }} />
      <Typography
        variant="caption"
        sx={{
          fontWeight: 700,
          color: "text.primary",
          bgcolor: "action.selected",
          px: 0.75,
          py: 0.125,
          borderRadius: 0.5,
          flexShrink: 0,
          lineHeight: 1.6,
        }}
      >
        {`v${compactSemanticVersion(version)}`}
      </Typography>
    </Box>
  );
}

export default StudyMetadataRow;
