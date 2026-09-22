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

import {
  type DefaultError,
  type QueryKey,
  type UnusedSkipTokenOptions,
  queryOptions,
} from "@tanstack/react-query";
import { queryClient } from "./queryClient";

////////////////////////////////////////////////////////////////
// Externally Mutated Data
////////////////////////////////////////////////////////////////

/**
 * Options for queries whose data can be mutated outside react-query's knowledge (legacy pages,
 * table mode, debug view, variant commands, server-side cascades), so the cache can't be
 * reliably invalidated.
 *
 * Data is treated as always stale: it refetches on every mount and window focus. Concurrent
 * readers of the same key still share a single fetch.
 *
 * Drop this only once ALL writers of the query invalidate the cache.
 */

export const EXTERNALLY_MUTATED = { staleTime: 0 } as const;

////////////////////////////////////////////////////////////////
// Query List
////////////////////////////////////////////////////////////////

type QueryListItemBase = object;

interface QueryListItemMetadata {
  isOptimistic?: boolean;
}

type QueryListItem<T extends QueryListItemBase = QueryListItemBase> = T & {
  _metadata?: QueryListItemMetadata;
};

const DEFAULT_LIST_ITEM_METADATA = {
  isOptimistic: false,
} as const satisfies QueryListItemMetadata;

function getQueryListItemMetadata(item: QueryListItem) {
  return item._metadata || DEFAULT_LIST_ITEM_METADATA;
}

export function isQueryListItemOptimistic(item: QueryListItem) {
  return getQueryListItemMetadata(item).isOptimistic;
}

export function createOptimisticListItem<T extends QueryListItemBase>(item: T): QueryListItem<T> {
  return {
    ...item,
    _metadata: {
      isOptimistic: true,
    },
  };
}

export function queryListOptions<
  TQueryFnData extends QueryListItemBase[],
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
>(
  options: Omit<
    UnusedSkipTokenOptions<TQueryFnData, TError, TData, TQueryKey>,
    "refetchOnWindowFocus" | "refetchOnReconnect" | "refetchOnMount"
  >,
) {
  /**
   * Block refetching if there are ongoing mutations that affect the list.
   *
   * Prevent refetching if the list is currently in an optimistic state, to avoid overwriting
   * pending changes with server data.
   *
   * @returns `false` if the query is mutating, `true` otherwise.
   * `true`: the query will refetch if the data is stale.
   * `false`: the query will not refetch.
   */
  const blockRefetchingIfMutating = () => {
    // By convention, mutations that affect a list should have a mutation key that starts
    // with the query key of the list
    return queryClient.isMutating({ mutationKey: options.queryKey }) === 0;
  };

  return queryOptions({
    ...options,
    refetchOnWindowFocus: blockRefetchingIfMutating,
    refetchOnReconnect: blockRefetchingIfMutating,
    refetchOnMount: blockRefetchingIfMutating,
  });
}
