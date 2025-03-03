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
  GridCellKind,
  type GridColumn,
  type Item,
  type NumberCell,
  type TextCell,
} from "@glideapps/glide-data-grid";
import { useMemo } from "react";
import { formatGridNumber } from "./Matrix/shared/utils";
import DataGrid from "@/components/common/DataGrid";

type CellValue = number | string;

interface DataGridViewerProps {
  data: CellValue[][];
  columns: GridColumn[];
}

function DataGridViewer({ data, columns }: DataGridViewerProps) {
  const getCellContent = useMemo(
    () => (cell: Item) => {
      const [col, row] = cell;
      const value = data[row]?.[col];

      if (typeof value === "number") {
        return {
          kind: GridCellKind.Number,
          data: value,
          displayData: formatGridNumber({ value, maxDecimals: 3 }),
          decimalSeparator: ".",
          thousandSeparator: " ",
          readonly: true,
          allowOverlay: false,
          contentAlign: "right",
        } satisfies NumberCell;
      }

      return {
        kind: GridCellKind.Text,
        data: String(value ?? ""),
        displayData: String(value ?? ""),
        readonly: true,
        allowOverlay: false,
      } satisfies TextCell;
    },
    [data],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DataGrid
      readOnly
      width="100%"
      height="100%"
      rows={data.length}
      columns={columns}
      getCellContent={getCellContent}
      rowMarkers="none"
      getCellsForSelection
    />
  );
}

export default DataGridViewer;
