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

import z from "zod";
import client from "../client";
import { tableModeCreationSchema, tableModeSchema, tableModeUpdateSchema } from "./schemas";
import type {
  DeleteTableModeParams,
  TableMode,
  TableModeCreation,
  UpdateTableModeParams,
} from "./types";

export async function getTableModes(): Promise<TableMode[]> {
  const { data } = await client.get("/v1/tablemode");
  return z.array(tableModeSchema).parse(data);
}

export async function createTableMode(params: TableModeCreation): Promise<TableMode> {
  const { data } = await client.post("/v1/tablemode", tableModeCreationSchema.parse(params));
  return tableModeSchema.parse(data);
}

export async function updateTableMode({
  tableId,
  ...update
}: UpdateTableModeParams): Promise<TableMode> {
  const { data } = await client.put(
    `/v1/tablemode/${tableId}`,
    tableModeUpdateSchema.parse(update),
  );

  return tableModeSchema.parse(data);
}

export async function deleteTableMode({ tableId }: DeleteTableModeParams) {
  await client.delete(`/v1/tablemode/${tableId}`);
}
