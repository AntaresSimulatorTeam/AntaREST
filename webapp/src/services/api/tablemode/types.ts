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

import type z from "zod";
import type {
  tableModeCreationSchema,
  tableModeSchema,
  tableModeTypeSchema,
  tableModeUpdateSchema,
} from "./schemas";

////////////////////////////////////////////////////////////////
// Response Types
////////////////////////////////////////////////////////////////

export type TableModeDTO = z.input<typeof tableModeSchema>;
export type TableMode = z.output<typeof tableModeSchema>;
export type TableModeType = z.infer<typeof tableModeTypeSchema>;

////////////////////////////////////////////////////////////////
// Request params
////////////////////////////////////////////////////////////////

export type TableModeColumnsForType<T extends TableModeType> = Extract<
  TableMode,
  { type: T }
>["columns"];

export type TableModeCreation = z.input<typeof tableModeCreationSchema>;

type TableModeUpdate = z.input<typeof tableModeUpdateSchema>;

export type UpdateTableModeParams = TableModeUpdate & { tableId: string };

export interface DeleteTableModeParams {
  tableId: string;
}
