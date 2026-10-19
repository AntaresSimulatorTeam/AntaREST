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

import { QueryObserver } from "@tanstack/react-query";
import { createQueryClient, deferred } from "@/tests/queryUtils";
import { invalidateQueriesAfterMutation } from "../invalidateQueriesAfterMutation";

describe("invalidateQueriesAfterMutation", () => {
  test("replaces an initial read without waiting for its stale response", async () => {
    const client = createQueryClient();
    const oldRead = deferred<string[]>();
    const queryKey = ["clusters"];
    const queryFn = vi.fn().mockReturnValueOnce(oldRead.promise).mockResolvedValue(["updated"]);

    // With no cached data, invalidation alone reuses the pre-mutation request (#6536).
    const observer = new QueryObserver(client, {
      queryKey,
      queryFn,
      staleTime: 0,
    });
    const unsubscribe = observer.subscribe(() => undefined);

    try {
      await invalidateQueriesAfterMutation(client, queryKey);

      expect(queryFn).toHaveBeenCalledTimes(2);
      expect(client.getQueryData(queryKey)).toEqual(["updated"]);

      oldRead.resolve(["outdated"]);
      await oldRead.promise;

      expect(client.getQueryData(queryKey)).toEqual(["updated"]);
    } finally {
      unsubscribe();
      client.clear();
    }
  });

  test("keeps an inactive list stale until it is read again", async () => {
    const client = createQueryClient();
    const oldRead = deferred<string[]>();
    const queryKey = ["clusters"];
    const queryFn = vi.fn().mockReturnValueOnce(oldRead.promise).mockResolvedValue(["updated"]);
    client.setQueryData(queryKey, ["original"]);

    const read = client.fetchQuery({ queryKey, queryFn, staleTime: 0 });

    try {
      await invalidateQueriesAfterMutation(client, queryKey);

      expect(queryFn).toHaveBeenCalledTimes(1);
      expect(client.getQueryState(queryKey)?.isInvalidated).toBe(true);

      oldRead.resolve(["outdated"]);
      await read;

      expect(client.getQueryState(queryKey)?.isInvalidated).toBe(true);
      expect(await client.fetchQuery({ queryKey, queryFn })).toEqual(["updated"]);
    } finally {
      client.clear();
    }
  });
});
