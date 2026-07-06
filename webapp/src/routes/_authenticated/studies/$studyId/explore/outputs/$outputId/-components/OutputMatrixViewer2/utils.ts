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

import { Column } from "@/components/Matrix/shared/constants";
import type { EnhancedGridColumn } from "@/components/Matrix/shared/types";
import type { DataType } from "../../-utils";

export interface ColumnsInfo {
  variables: string[];
  units: string[];
  stats: string[];
}

export const DATE_GRID_COLUMN = {
  id: "date",
  title: "Date",
  type: Column.DateTime,
  editable: false,
} as const satisfies EnhancedGridColumn;

/**
 * Check if the given data type is a cluster data type.
 * Note: Short-term storages are considered as clusters in this context.
 *
 * @param dataType - The data type to check.
 * @returns True if the data type is a cluster data type, false otherwise.
 */
export function isClusterDataType(dataType: DataType) {
  return (
    // Thermal clusters
    dataType === "details" ||
    // Renewable clusters
    dataType === "details-res" ||
    // Short-term storages
    dataType === "details-STstorage"
  );
}
