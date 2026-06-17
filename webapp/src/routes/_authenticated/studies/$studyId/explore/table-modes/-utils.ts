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

import type { RouterListViewItem } from "@/components/page/list/RouterListView";
import { isQueryListItemOptimistic } from "@/queries/utils";
import { TABLE_MODE_COLUMNS_BY_TYPE } from "@/services/api/studies/tableMode/constants";
import type {
  TableMode,
  TableModeColumnsForType,
  TableModeType,
} from "@/services/api/tablemode/types";
import { linkOptions } from "@tanstack/react-router";
import { sortByProp } from "ramda-adjunct";

export interface TableTemplate<T extends TableModeType = TableModeType> {
  name: string;
  type: T;
  columns: TableModeColumnsForType<T>;
}

export function getTableColumnsForType(type: TableModeType): readonly string[] {
  // Arrays have a numeric index signature because of `as const`
  return TABLE_MODE_COLUMNS_BY_TYPE[type];
}

export function tableModesToList(tableModes: TableMode[]): RouterListViewItem[] {
  const list = tableModes.map((tm) => ({
    id: tm.id,
    label: tm.name,
    linkOptions: linkOptions({
      to: ".",
      params: { tableModeId: tm.id },
    }),
    loading: isQueryListItemOptimistic(tm),
  }));

  return sortByProp("label", list);
}
