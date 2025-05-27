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

import { Stack, Chip } from "@mui/material";
import { useFilterSummary } from "../hooks/useFilterSummary";
import { CHIP_STYLES } from "../styles";
import type { FilterState } from "../types";

interface FilterSummaryChipsProps {
  filter: FilterState;
  isPreviewActive: boolean;
}

function FilterSummaryChips({ filter, isPreviewActive }: FilterSummaryChipsProps) {
  const { columnFilterText, rowFilterTexts } = useFilterSummary(filter);

  const getChipStyles = () => ({
    ...CHIP_STYLES.base,
    ...(isPreviewActive && CHIP_STYLES.preview),
  });

  return (
    <Stack direction="row" spacing={0.25} flexWrap="wrap" useFlexGap>
      {columnFilterText && (
        <Chip
          label={columnFilterText}
          size="small"
          color="primary"
          variant="outlined"
          sx={getChipStyles()}
        />
      )}
      {rowFilterTexts.map((text, index) => (
        <Chip
          key={`row-filter-${index}-${text}`}
          label={text}
          size="small"
          color="primary"
          variant="outlined"
          sx={getChipStyles()}
        />
      ))}
    </Stack>
  );
}

export default FilterSummaryChips;
