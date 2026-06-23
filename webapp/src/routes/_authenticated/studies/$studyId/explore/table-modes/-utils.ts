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
import type { TableMode } from "@/services/api/tablemode/types";
import { linkOptions } from "@tanstack/react-router";
import { sortByProp } from "ramda-adjunct";

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
