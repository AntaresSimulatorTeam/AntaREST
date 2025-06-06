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

import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import FilterAltOffIcon from "@mui/icons-material/FilterAltOff";
import CloseIcon from "@mui/icons-material/Close";
import { useTranslation } from "react-i18next";
import { DESIGN_TOKENS } from "../styles";

interface DrawerHeaderProps {
  onResetFilters: () => void;
  onClose: () => void;
}

function DrawerHeader({ onResetFilters, onClose }: DrawerHeaderProps) {
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        mb: DESIGN_TOKENS.spacing.xl,
        flexShrink: 0,
      }}
    >
      <Typography sx={{ fontSize: DESIGN_TOKENS.fontSize.lg, fontWeight: 500 }}>
        {t("matrix.filter.title")}
      </Typography>
      <Box>
        <Tooltip title={t("matrix.filter.resetFilters")}>
          <IconButton onClick={onResetFilters} size="small">
            <FilterAltOffIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t("matrix.filter.close")}>
          <IconButton onClick={onClose} size="small">
            <CloseIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}

export default DrawerHeader;
