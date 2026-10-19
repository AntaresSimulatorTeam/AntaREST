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

import type { QueryClient, QueryKey } from "@tanstack/react-query";

/**
 * Cancel superseded reads before invalidating the queries affected by a successful write.
 * Default invalidation deduplicates initial reads and does not refetch inactive queries.
 * Explicit cancellation prevents either from marking an old result fresh after the write,
 * without waiting for the old request to finish. Active queries then fetch current data.
 * Imperative callers awaiting an initial read must handle its cancellation.
 *
 * @see https://github.com/TanStack/query/issues/6536
 *
 * @param queryClient - The consumers' QueryClient.
 * @param queryKey - Prefix of the queries affected by the successful mutation.
 * @returns Completion of invalidation and active refetches. Read failures stay query errors.
 */
export async function invalidateQueriesAfterMutation(queryClient: QueryClient, queryKey: QueryKey) {
  await queryClient.cancelQueries({ queryKey });
  await queryClient.invalidateQueries({ queryKey });
}
