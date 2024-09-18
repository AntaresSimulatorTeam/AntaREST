/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { v4 as uuidv4 } from "uuid";
import {
  TableModeColumnsForType,
  TableModeType,
} from "../../../../../services/api/studies/tableMode/types";
import { TABLE_MODE_COLUMNS_BY_TYPE } from "../../../../../services/api/studies/tableMode/constants";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface TableTemplate<T extends TableModeType = TableModeType> {
  id: string;
  name: string;
  type: T;
  columns: TableModeColumnsForType<T>;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Allows to check columns validity for specified type. Creates a table template with unique ID, name, type, and columns configuration.
 * This function is intended to define the structure and type of data that a table can hold.
 *
 * @param name - The name of the table template.
 * @param type - The type of the table, determining the allowed columns and their configuration based on the table mode type.
 * @param columns - The configuration of columns specific to the table mode type.
 * @returns A table template object including a unique ID, name, type, and columns configuration.
 */
export function createTableTemplate<T extends TableModeType>(
  name: string,
  type: T,
  columns: TableModeColumnsForType<T>,
): TableTemplate<T> {
  return { id: uuidv4(), name, type, columns };
}

export function getTableColumnsForType(type: TableModeType): readonly string[] {
  // Arrays have a numeric index signature because of `as const`
  return TABLE_MODE_COLUMNS_BY_TYPE[type];
}
