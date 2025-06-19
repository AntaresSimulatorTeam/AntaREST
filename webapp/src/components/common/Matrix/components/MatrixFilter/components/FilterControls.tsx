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

import FilterListIcon from "@mui/icons-material/FilterList";
import { Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { BUTTON_STYLES, DESIGN_TOKENS } from "../styles";

interface FilterControlsProps {
  isFilterActive: boolean;
  onToggleFilter: () => void;
}

function FilterControls({ isFilterActive, onToggleFilter }: FilterControlsProps) {
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        display: "flex",
        gap: DESIGN_TOKENS.spacing.md,
        flexShrink: 0,
      }}
    >
      <Button
        variant={isFilterActive ? "contained" : "outlined"}
        color={isFilterActive ? "primary" : "inherit"}
        onClick={onToggleFilter}
        startIcon={<FilterListIcon fontSize="small" />}
        size="small"
        sx={BUTTON_STYLES.compact}
      >
        {isFilterActive ? t("matrix.filter.active") : t("matrix.filter.inactive")}
      </Button>
    </Box>
  );
}

export default FilterControls;
