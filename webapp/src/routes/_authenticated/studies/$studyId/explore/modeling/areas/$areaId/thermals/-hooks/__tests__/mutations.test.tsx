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

import { reserveKeys } from "@/queries/reserves/keys";
import { thermalKeys } from "@/queries/thermals/keys";
import { thermalQueries } from "@/queries/thermals/queries";
import * as api from "@/services/api/studies/areas/thermals";
import type { ThermalCluster } from "@/services/api/studies/areas/thermals/types";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import useCreateThermalCluster from "../useCreateThermalCluster";
import useDeleteThermalClusters from "../useDeleteThermalClusters";
import useDuplicateThermalCluster from "../useDuplicateThermalCluster";
import useThermalClusters from "../useThermalClusters";
import useUpdateThermalCluster from "../useUpdateThermalCluster";
import { cluster, deferred } from "./fixtures";

const { dispatch, synthesis } = vi.hoisted(() => ({ dispatch: vi.fn(), synthesis: vi.fn() }));
vi.mock("@/services/api/client", () => ({ default: {} }));
vi.mock("@/i18n", () => ({ default: { t: (key: string) => key, language: "en" } }));
vi.mock("@/services/api/studies/areas/thermals");
vi.mock("@/redux/hooks/useAppDispatch", () => ({ default: () => dispatch }));
vi.mock("@/redux/ducks/studySyntheses", () => ({ setStudySynthesis: synthesis }));

const scope = { studyId: "study", areaId: "area" };
const key = thermalKeys.list(scope.studyId, scope.areaId);
let client: QueryClient;
function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
function useMutations() {
  return {
    create: useCreateThermalCluster(scope),
    duplicate: useDuplicateThermalCluster(scope),
    update: useUpdateThermalCluster(scope),
    delete: useDeleteThermalClusters(scope),
  };
}

beforeEach(() => {
  vi.resetAllMocks();
  client = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000, retry: false } } });
  client.setQueryData(key, [cluster]);
  vi.mocked(api.getThermalClusters).mockResolvedValue([cluster]);
  vi.mocked(api.createThermalCluster).mockResolvedValue(cluster);
  vi.mocked(api.duplicateThermalCluster).mockResolvedValue(cluster);
  vi.mocked(api.updateThermalCluster).mockResolvedValue(cluster);
  vi.mocked(api.deleteThermalClusters).mockResolvedValue(undefined);
});
afterEach(() => client.clear());

const operations = ["create", "duplicate", "update", "delete"] as const;
function run(
  operation: (typeof operations)[number],
  mutations: ReturnType<typeof useMutations>,
): Promise<unknown> {
  switch (operation) {
    case "create":
      return mutations.create.mutateAsync({ ...scope, values: { name: "New" } });
    case "duplicate":
      return mutations.duplicate.mutateAsync({ ...scope, clusterId: cluster.id, newName: "Copy" });
    case "update":
      return mutations.update.mutateAsync({
        ...scope,
        clusterId: cluster.id,
        values: { enabled: false },
      });
    case "delete":
      return mutations.delete.mutateAsync({ ...scope, clusterIds: [cluster.id] });
  }
}

test.each(operations)(
  "%s invalidates its area and refreshes synthesis only after success",
  async (operation) => {
    const untouched = [thermalKeys.list("other", "area"), thermalKeys.list("study", "other")];
    const reserves = [
      reserveKeys.certifications("study", "area", "thermals"),
      reserveKeys.symmetries("study", "area", "thermals"),
    ];
    untouched.push(
      reserveKeys.certifications("study", "area", "storages"),
      reserveKeys.symmetries("study", "other", "thermals"),
    );
    [...untouched, ...reserves].forEach((key) => {
      client.setQueryData(key, []);
    });
    const { result } = renderHook(useMutations, { wrapper });
    await act(async () => {
      await run(operation, result.current);
    });
    expect(client.getQueryState(key)?.isInvalidated).toBe(true);
    expect(client.getQueryData(key)).toEqual([cluster]);
    expect(synthesis).toHaveBeenCalledWith("study");
    expect(dispatch).toHaveBeenCalledTimes(1);
    reserves.forEach((key) => {
      expect(client.getQueryState(key)?.isInvalidated).toBe(operation === "delete");
    });
    untouched.forEach((key) => {
      expect(client.getQueryState(key)?.isInvalidated).toBe(false);
    });
  },
);

test.each(operations)(
  "failed %s preserves cached rows and propagates the error for the UI rollback",
  async (operation) => {
    const error = new Error("write failed");
    vi.mocked(api.createThermalCluster).mockRejectedValue(error);
    vi.mocked(api.duplicateThermalCluster).mockRejectedValue(error);
    vi.mocked(api.updateThermalCluster).mockRejectedValue(error);
    vi.mocked(api.deleteThermalClusters).mockRejectedValue(error);
    const { result } = renderHook(useMutations, { wrapper });
    await act(async () => {
      await expect(run(operation, result.current)).rejects.toBe(error);
    });
    expect(client.getQueryData(key)).toEqual([cluster]);
    expect(client.getQueryState(key)?.isInvalidated).toBe(false);
    expect(dispatch).not.toHaveBeenCalled();
  },
);

test("mutation stays pending until its active list refresh finishes without optimistic cache writes", async () => {
  const response = deferred<ThermalCluster[]>();
  vi.mocked(api.getThermalClusters).mockReturnValue(response.promise);
  const { result } = renderHook(
    () => ({ list: useThermalClusters(scope), mutations: useMutations() }),
    { wrapper },
  );
  let write: Promise<unknown>;
  act(() => {
    write = run("update", result.current.mutations);
  });
  await waitFor(() => expect(api.getThermalClusters).toHaveBeenCalledTimes(1));
  expect(result.current.mutations.update.isPending).toBe(true);
  expect(client.getQueryData(key)).toEqual([cluster]);
  await act(async () => {
    response.resolve([{ ...cluster, enabled: false }]);
    await write;
  });
  await waitFor(() => expect(result.current.mutations.update.isSuccess).toBe(true));
  expect(result.current.list.data?.[0].enabled).toBe(false);
});

test("a failed concurrent write cannot roll back a successful write, even after unmount", async () => {
  const creation = deferred<ThermalCluster>();
  const deletion = deferred<void>();
  vi.mocked(api.createThermalCluster).mockReturnValue(creation.promise);
  vi.mocked(api.deleteThermalClusters).mockReturnValue(deletion.promise);
  const { result, unmount } = renderHook(useMutations, { wrapper });
  let created: Promise<unknown>;
  let deleted: Promise<unknown>;
  act(() => {
    created = run("create", result.current);
    deleted = run("delete", result.current).catch((error) => error);
  });
  unmount();
  const newCluster = { ...cluster, id: "new", name: "New" };
  await act(async () => {
    creation.resolve(newCluster);
    await created;
  });
  vi.mocked(api.getThermalClusters).mockResolvedValue([cluster, newCluster]);
  await client.fetchQuery(thermalQueries.list("study", "area"));
  await act(async () => {
    deletion.reject(new Error("delete failed"));
    await deleted;
  });
  expect(client.getQueryData(key)).toEqual([cluster, newCluster]);
  expect(dispatch).toHaveBeenCalledTimes(1);
});

test("a late response from an earlier refresh cannot overwrite a newer successful mutation", async () => {
  const firstRefresh = deferred<ThermalCluster[]>();
  const secondRefresh = deferred<ThermalCluster[]>();
  vi.mocked(api.getThermalClusters)
    .mockReturnValueOnce(firstRefresh.promise)
    .mockReturnValueOnce(secondRefresh.promise);
  const { result } = renderHook(
    () => ({ list: useThermalClusters(scope), mutations: useMutations() }),
    { wrapper },
  );
  let firstWrite: Promise<unknown>;
  let secondWrite: Promise<unknown>;
  act(() => {
    firstWrite = run("create", result.current.mutations);
  });
  await waitFor(() => expect(api.getThermalClusters).toHaveBeenCalledTimes(1));
  act(() => {
    secondWrite = run("update", result.current.mutations);
  });
  await waitFor(() => expect(api.getThermalClusters).toHaveBeenCalledTimes(2));
  const newest = [{ ...cluster, enabled: false }];
  await act(async () => {
    secondRefresh.resolve(newest);
    await secondWrite;
  });
  await act(async () => {
    firstRefresh.resolve([cluster]);
    await firstWrite;
  });
  expect(client.getQueryData(key)).toEqual(newest);
});
