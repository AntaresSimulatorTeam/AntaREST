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

import {
  generateDataColumns,
  generateResultColumns,
  groupResultColumns,
} from "@/components/common/Matrix/shared/utils";
import { Box } from "@mui/material";
import type { DigestMatrixData } from "./types";
import { GridOff } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import EmptyView from "../../page/EmptyView";
import DataGridViewer from "../../DataGridViewer";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";

const isGroupedColumns = (columns: string[] | string[][]): columns is string[][] => {
  return Array.isArray(columns[0]);
};

interface DigestMatrixProps {
  matrix: DigestMatrixData;
}

function DigestMatrix({ matrix }: DigestMatrixProps) {
  const [t] = useTranslation();
  const { isDarkMode } = useThemeColorScheme();

  const columns = matrix.groupedColumns
    ? groupResultColumns(
        generateResultColumns({
          titles: isGroupedColumns(matrix.columns) ? matrix.columns : [],
          width: 130,
        }),
        isDarkMode,
      )
    : generateDataColumns({
        timeSeriesColumns: false,
        count: matrix.columns.length,
        customColumns: !isGroupedColumns(matrix.columns) ? matrix.columns : undefined,
      });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ width: 1, height: "calc(100vh - 350px)" }}>
        {!matrix.data[0]?.length ? (
          <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOff} />
        ) : (
          <DataGridViewer data={matrix.data} columns={columns} />
        )}
      </Box>
    </Box>
  );
}

export default DigestMatrix;
