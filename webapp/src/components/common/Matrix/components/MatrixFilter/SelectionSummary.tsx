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

import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { SelectionSummaryProps } from "./types";

function SelectionSummary({ filteredData }: SelectionSummaryProps) {
  const { t } = useTranslation();

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle2" color="text.secondary">
        {t("matrix.filter.selectionSummary")}
      </Typography>
      <Typography>
        {t("matrix.filter.selectedRows")}: {filteredData.rowsIndices.length}
      </Typography>
      <Typography>
        {t("matrix.filter.selectedColumns")}: {filteredData.columnsIndices.length}
      </Typography>
      <Typography>
        {t("matrix.filter.selectedCells")}:{" "}
        {filteredData.rowsIndices.length * filteredData.columnsIndices.length}
      </Typography>
    </Box>
  );
}

export default SelectionSummary;
