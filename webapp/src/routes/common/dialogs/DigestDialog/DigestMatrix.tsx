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
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import { GridOff } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import DataGridViewer from "../../DataGridViewer";
import EmptyView from "../../page/EmptyView";
import type { DigestMatrixData } from "./types";

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
        isTimeSeries: false,
        count: matrix.columns.length,
        customColumns: !isGroupedColumns(matrix.columns) ? matrix.columns : undefined,
      });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {!matrix.data[0]?.length ? (
        <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOff} />
      ) : (
        <DataGridViewer
          data={matrix.data}
          columns={columns}
          freezeColumns={1} // First column (areas) should be always visible
          rowMarkers="checkbox"
        />
      )}
    </>
  );
}

export default DigestMatrix;
