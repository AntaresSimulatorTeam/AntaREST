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

import type { DeepPartial } from "react-hook-form";
import type { StudyMetadata } from "../../../../types/types";
import type { TABLE_MODE_COLUMNS_BY_TYPE, TABLE_MODE_TYPES } from "./constants";

export type TableModeType = (typeof TABLE_MODE_TYPES)[number];

export type TableModeColumnsForType<T extends TableModeType> = Array<
  (typeof TABLE_MODE_COLUMNS_BY_TYPE)[T][number]
>;

export type TableData = Record<string, Record<string, string | boolean | number>>;

export interface GetTableModeParams<T extends TableModeType> {
  studyId: StudyMetadata["id"];
  tableType: T;
  columns: TableModeColumnsForType<T>;
}

export interface SetTableModeParams {
  studyId: StudyMetadata["id"];
  tableType: TableModeType;
  data: DeepPartial<TableData>;
}
