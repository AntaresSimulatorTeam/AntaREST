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

import { queryClient } from "@/queries/queryClient";
import { getThermalClusters } from "@/services/api/studies/areas/thermals";
import { thermalKeys } from "../keys";
import { thermalMutations } from "../mutations";
import { thermalQueries } from "../queries";

vi.mock("@/services/api/studies/areas/thermals", () => ({
  getThermalClusters: vi.fn(),
  createThermalCluster: vi.fn(),
  updateThermalCluster: vi.fn(),
  duplicateThermalCluster: vi.fn(),
  deleteThermalClusters: vi.fn(),
}));

afterEach(() => {
  queryClient.clear();
  vi.resetAllMocks();
});

function getRefetchDecisions(options: ReturnType<typeof thermalQueries.list>) {
  const query = queryClient.getQueryCache().build(queryClient, {
    ...options,
    queryKey: [...options.queryKey],
  });
  return [options.refetchOnMount, options.refetchOnWindowFocus, options.refetchOnReconnect].map(
    (condition) => (typeof condition === "function" ? condition(query) : condition),
  );
}

test("shares concurrent list requests and isolates studies and areas", async () => {
  vi.mocked(getThermalClusters).mockResolvedValue([]);

  await Promise.all([
    queryClient.fetchQuery(thermalQueries.list("study-1", "area-1")),
    queryClient.fetchQuery(thermalQueries.list("study-1", "area-1")),
    queryClient.fetchQuery(thermalQueries.list("study-1", "area-2")),
    queryClient.fetchQuery(thermalQueries.list("study-2", "area-1")),
  ]);

  expect(getThermalClusters).toHaveBeenCalledTimes(3);
  expect(getThermalClusters).toHaveBeenCalledWith({ studyId: "study-1", areaId: "area-1" });
  expect(getThermalClusters).toHaveBeenCalledWith({ studyId: "study-1", areaId: "area-2" });
  expect(getThermalClusters).toHaveBeenCalledWith({ studyId: "study-2", areaId: "area-1" });
});

test("retains immediate staleness while legacy writers bypass the cache", async () => {
  vi.mocked(getThermalClusters).mockResolvedValue([]);

  const options = thermalQueries.list("study-1", "area-1");
  await queryClient.fetchQuery(options);
  await queryClient.fetchQuery(options);

  expect(getThermalClusters).toHaveBeenCalledTimes(2);
  expect(options.staleTime).toBe(0);
});

test.each(["create", "update", "duplicate", "delete"] as const)(
  "%s blocks list refetching only in the affected area while pending",
  async (operation) => {
    let finish: (() => void) | undefined;
    const pending = new Promise<void>((resolve) => {
      finish = resolve;
    });
    const mutation = queryClient.getMutationCache().build(queryClient, {
      mutationKey: thermalMutations[operation]("study-1", "area-1").mutationKey,
      mutationFn: () => pending,
    });
    const result = mutation.execute(undefined);

    const options = thermalQueries.list("study-1", "area-1");
    const otherAreaOptions = thermalQueries.list("study-1", "area-2");
    const otherStudyOptions = thermalQueries.list("study-2", "area-1");

    try {
      expect(queryClient.isMutating({ mutationKey: thermalKeys.list("study-1", "area-1") })).toBe(
        1,
      );
      expect(getRefetchDecisions(options)).toEqual([false, false, false]);
      expect(getRefetchDecisions(otherAreaOptions)).toEqual([true, true, true]);
      expect(getRefetchDecisions(otherStudyOptions)).toEqual([true, true, true]);
    } finally {
      finish?.();
      await result;
    }

    expect(getRefetchDecisions(options)).toEqual([true, true, true]);
  },
);
