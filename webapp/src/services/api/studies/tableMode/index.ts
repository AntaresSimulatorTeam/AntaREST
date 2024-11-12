/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import client from "../../client";
import { format } from "../../../../utils/stringUtils";
import type {
  GetTableModeParams,
  SetTableModeParams,
  TableData,
  TableModeType,
} from "./types";

const TABLE_MODE_API_URL = `/v1/studies/{studyId}/table-mode/{tableType}`;

export async function getTableMode<T extends TableModeType>(
  params: GetTableModeParams<T>,
) {
  const { studyId, tableType, columns } = params;
  const url = format(TABLE_MODE_API_URL, { studyId, tableType });

  const { data } = await client.get<TableData>(url, {
    params: columns.length > 0 ? { columns: columns.join(",") } : {},
  });

  return data;
}

export async function setTableMode(params: SetTableModeParams) {
  const { studyId, tableType, data } = params;
  const url = format(TABLE_MODE_API_URL, { studyId, tableType });
  await client.put<null>(url, data);
}
