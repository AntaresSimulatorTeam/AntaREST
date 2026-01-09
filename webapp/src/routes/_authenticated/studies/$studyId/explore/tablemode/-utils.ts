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

import { TABLE_MODE_COLUMNS_BY_TYPE } from "@/services/api/studies/tableMode/constants";
import type {
  TableModeColumnsForType,
  TableModeType,
} from "@/services/api/studies/tableMode/types";

export interface TableTemplate<T extends TableModeType = TableModeType> {
  name: string;
  type: T;
  columns: TableModeColumnsForType<T>;
}

export function getTableColumnsForType(type: TableModeType): readonly string[] {
  // Arrays have a numeric index signature because of `as const`
  return TABLE_MODE_COLUMNS_BY_TYPE[type];
}
