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

import "./setup";

import { reserveKeys } from "@/queries/reserves/keys";
import { thermalKeys } from "@/queries/thermals/keys";
import * as api from "@/services/api/studies/areas/thermals";
import type { QueryClient } from "@tanstack/react-query";
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import { act, renderHook, waitFor } from "@testing-library/react";
import useCreateThermalCluster from "../useCreateThermalCluster";
import useDeleteThermalClusters from "../useDeleteThermalClusters";
import useThermalClusters from "../useThermalClusters";
import { cluster } from "./fixtures";

const scope = { studyId: "study", areaId: "area" };
const key = thermalKeys.list(scope.studyId, scope.areaId);
let client: QueryClient;
let wrapper: ReturnType<typeof createQueryWrapper>;

beforeEach(() => {
  client = createQueryClient();
  wrapper = createQueryWrapper(client);
  client.setQueryData(key, [cluster]);

  vi.mocked(api.getThermalClusters).mockReset().mockResolvedValue([cluster]);
  vi.mocked(api.createThermalCluster).mockReset().mockResolvedValue(cluster);
  vi.mocked(api.deleteThermalClusters).mockReset().mockResolvedValue(undefined);
});

afterEach(() => client.clear());

describe("Thermal mutations", () => {
  test("deleting a cluster invalidates its list and dependent reserves", async () => {
    const affected = [
      key,
      reserveKeys.certifications("study", "area", "thermals"),
      reserveKeys.symmetries("study", "area", "thermals"),
    ];

    const untouched = [
      thermalKeys.list("other", "area"),
      thermalKeys.list("study", "other"),
      reserveKeys.certifications("study", "area", "storages"),
      reserveKeys.symmetries("study", "other", "thermals"),
    ];

    [...affected, ...untouched].forEach((key) => {
      client.setQueryData(key, []);
    });

    const { result } = renderHook(() => useDeleteThermalClusters(scope), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ ...scope, clusterIds: [cluster.id] });
    });

    affected.forEach((key) => {
      expect(client.getQueryState(key)?.isInvalidated).toBe(true);
    });
    untouched.forEach((key) => {
      expect(client.getQueryState(key)?.isInvalidated).toBe(false);
    });
  });

  test("a refresh failure does not fail a successful write", async () => {
    const readError = new Error("refresh failed");
    vi.mocked(api.getThermalClusters).mockRejectedValue(readError);

    const { result } = renderHook(
      () => ({ list: useThermalClusters(scope), create: useCreateThermalCluster(scope) }),
      { wrapper },
    );

    // The server already committed the write: a read failure must not trigger rollback.
    await act(async () => {
      await expect(
        result.current.create.mutateAsync({ ...scope, values: { name: "Gas" } }),
      ).resolves.toEqual(cluster);
    });

    await waitFor(() => expect(result.current.list.error).toBe(readError));
    expect(result.current.create.isSuccess).toBe(true);
    expect(client.getQueryState(key)?.isInvalidated).toBe(true);
  });
});
