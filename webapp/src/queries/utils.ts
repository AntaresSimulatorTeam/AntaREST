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

import type { QueryList, QueryListItem, QueryListItemBase, QueryListItemMetadata } from "./types";

const DEFAULT_LIST_ITEM_METADATA = {
  isOptimistic: false,
} as const satisfies QueryListItemMetadata;

export function queryList<T extends QueryListItemBase>(list: T[]): QueryList<T> {
  return list;
}

export function getQueryListItemMetadata(item: QueryListItem) {
  return item._metadata || DEFAULT_LIST_ITEM_METADATA;
}

export function isQueryListItemOptimistic(item: QueryListItem) {
  return getQueryListItemMetadata(item).isOptimistic;
}

export function isQueryListMutating<T extends QueryListItemBase>(list: QueryList<T>) {
  return list.some(isQueryListItemOptimistic);
}
