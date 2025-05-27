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

import { Box, Button, Tooltip } from "@mui/material";
import FilterListIcon from "@mui/icons-material/FilterList";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import { useTranslation } from "react-i18next";
import { DESIGN_TOKENS, BUTTON_STYLES } from "../styles";

interface FilterControlsProps {
  isFilterActive: boolean;
  isPreviewActive: boolean;
  onToggleFilter: () => void;
  onTogglePreview: () => void;
}

function FilterControls({
  isFilterActive,
  isPreviewActive,
  onToggleFilter,
  onTogglePreview,
}: FilterControlsProps) {
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        display: "flex",
        gap: DESIGN_TOKENS.spacing.md,
        mb: DESIGN_TOKENS.spacing.xl,
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

      {isFilterActive && (
        <Tooltip
          title={t(
            isPreviewActive ? "matrix.filter.preview.active" : "matrix.filter.preview.inactive",
          )}
        >
          <Button
            variant="outlined"
            color={isPreviewActive ? "info" : "inherit"}
            onClick={onTogglePreview}
            size="small"
            sx={BUTTON_STYLES.compactIconOnly}
          >
            {isPreviewActive ? (
              <VisibilityIcon fontSize="small" />
            ) : (
              <VisibilityOffIcon fontSize="small" />
            )}
          </Button>
        </Tooltip>
      )}
    </Box>
  );
}

export default FilterControls;
