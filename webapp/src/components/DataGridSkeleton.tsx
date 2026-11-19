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

import { type GridColumn, GridCellKind } from "@glideapps/glide-data-grid";
import DataGrid from "./DataGrid";

const SKELETON_COLUMNS: GridColumn[] = Array.from({ length: 5 }, (_, index) => ({
  id: index.toString(),
  title: "",
  width: 100,
}));

const SKELETON_CELL = {
  kind: GridCellKind.Text,
  data: "",
  displayData: "",
  allowOverlay: false,
} as const;

interface DataGridSkeletonProps {
  /**
   * Uses the read-only colors, to match the real grid and avoid a flash when data arrives.
   * Visual only: the skeleton is never editable.
   */
  readOnly?: boolean;
}

function DataGridSkeleton({ readOnly }: DataGridSkeletonProps) {
  return (
    <DataGrid
      getCellContent={() => SKELETON_CELL}
      columns={SKELETON_COLUMNS}
      rows={10}
      readOnly={readOnly}
      isLoading
    />
  );
}

export default DataGridSkeleton;
