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

import type { DeepPartial } from "react-hook-form";
import type { TableModeColumnsForType, TableModeType } from "../../tablemode/types";
import type { Study } from "../types";

export type TableModeData = Record<string, Record<string, string | boolean | number>>;

export interface GetTableModeParams<T extends TableModeType> {
  studyId: Study["id"];
  tableType: T;
  columns: TableModeColumnsForType<T>;
}

export interface SetTableModeParams {
  studyId: Study["id"];
  tableType: TableModeType;
  data: DeepPartial<TableModeData>;
}
