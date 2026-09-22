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
import { thermalQueries } from "@/queries/thermals/queries";
import * as legacy from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/-utils";
import client from "@/services/api/client";
import { ZodError } from "zod";
import * as api from "..";
import type { ThermalCluster } from "../types";

vi.mock("@/services/api/client", () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

const studyId = "study-1";
const areaId = "area-1";
const clusterId = "gas cluster";
const listUrl = `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`;
const cluster: ThermalCluster = {
  id: "Gas Cluster",
  name: "Gas Cluster",
  group: "custom gas",
  enabled: true,
  unitCount: 2,
  nominalCapacity: 100,
  mustRun: false,
  minStablePower: 10,
  spinning: 0,
  minUpTime: 1,
  minDownTime: 1,
  marginalCost: 20,
  fixedCost: 0,
  startupCost: 0,
  marketBidCost: 20,
  spreadCost: 0,
  genTs: "use global",
  volatilityForced: 0,
  volatilityPlanned: 0,
  lawForced: "uniform",
  lawPlanned: "uniform",
  co2: 0,
};

const versionedProperties = {
  so2: 1,
  nh3: 2,
  nox: 3,
  nmvoc: 4,
  pm25: 5,
  pm5: 6,
  pm10: 7,
  op1: 8,
  op2: 9,
  op3: 10,
  op4: 11,
  op5: 12,
  costGeneration: "useCostTimeseries",
  efficiency: 50,
  variableOMCost: 15,
} satisfies Partial<ThermalCluster>;

const callers = [
  {
    name: "service API",
    list: () => api.getThermalClusters({ studyId, areaId }),
    detail: () => api.getThermalCluster({ studyId, areaId, clusterId }),
    create: () => api.createThermalCluster({ studyId, areaId, values: { name: "New cluster" } }),
    update: () =>
      api.updateThermalCluster({ studyId, areaId, clusterId, values: { enabled: false } }),
    duplicate: () => api.duplicateThermalCluster({ studyId, areaId, clusterId, newName: "Copy" }),
    delete: () => api.deleteThermalClusters({ studyId, areaId, clusterIds: [clusterId, "other"] }),
  },
  {
    name: "legacy compatibility helpers",
    list: () => legacy.getThermalClusters(studyId, areaId),
    detail: () => legacy.getThermalCluster(studyId, areaId, clusterId),
    create: () => legacy.createThermalCluster(studyId, areaId, { name: "New cluster" }),
    update: () => legacy.updateThermalCluster(studyId, areaId, clusterId, { enabled: false }),
    duplicate: () => legacy.duplicateThermalCluster(studyId, areaId, clusterId, "Copy"),
    delete: () => legacy.deleteThermalClusters(studyId, areaId, [clusterId, "other"]),
  },
];

beforeEach(() => {
  vi.resetAllMocks();
});

afterEach(() => {
  queryClient.clear();
});

describe.each(callers)("$name", (caller) => {
  test("retains every list property and normalizes IDs without mutating the response", async () => {
    const response = { ...cluster, so2: null, costGeneration: null };
    vi.mocked(client.get).mockResolvedValue({ data: [response] });

    const result = await caller.list();

    expect(client.get).toHaveBeenCalledTimes(1);
    expect(client.get).toHaveBeenCalledWith(listUrl);
    expect(result).toEqual([{ ...response, id: clusterId }]);
    expect(response.id).toBe("Gas Cluster");
  });

  test("preserves the single-item response, including legacy ID casing", async () => {
    vi.mocked(client.get).mockResolvedValue({ data: cluster });

    expect(await caller.detail()).toEqual(cluster);
    expect(client.get).toHaveBeenCalledTimes(1);
    expect(client.get).toHaveBeenCalledWith(`${listUrl}/${clusterId}`);
  });

  test.each([
    { version: "before 8.6", properties: {} },
    {
      version: "unsupported versioned fields returned as null",
      properties: Object.fromEntries(Object.keys(versionedProperties).map((key) => [key, null])),
    },
    { version: "8.7 and later", properties: versionedProperties },
  ])("preserves version-dependent properties: $version", async ({ properties }) => {
    const response = { ...cluster, ...properties };
    vi.mocked(client.get).mockResolvedValue({ data: response });

    expect(await caller.detail()).toEqual(response);
  });

  test.each(["list", "detail", "create", "update", "duplicate"] as const)(
    "%s rejects malformed responses at the API boundary",
    async (operation) => {
      const invalidCluster = { ...cluster, genTs: "unknown behavior" };
      const response = { data: operation === "list" ? [invalidCluster] : invalidCluster };
      vi.mocked(client.get).mockResolvedValue(response);
      vi.mocked(client.post).mockResolvedValue(response);
      vi.mocked(client.patch).mockResolvedValue(response);

      await expect(caller[operation]()).rejects.toBeInstanceOf(ZodError);
    },
  );

  test("creates a cluster from a name-only payload", async () => {
    vi.mocked(client.post).mockResolvedValue({ data: cluster });

    expect(await caller.create()).toEqual(cluster);
    expect(client.post).toHaveBeenCalledTimes(1);
    expect(client.post).toHaveBeenCalledWith(listUrl, { name: "New cluster" });
  });

  test("patches only supplied values", async () => {
    const updated = { ...cluster, enabled: false };
    vi.mocked(client.patch).mockResolvedValue({ data: updated });

    expect(await caller.update()).toEqual(updated);
    expect(client.patch).toHaveBeenCalledTimes(1);
    expect(client.patch).toHaveBeenCalledWith(`${listUrl}/${clusterId}`, {
      enabled: false,
    });
  });

  test("duplicates through the dedicated endpoint and newName query parameter", async () => {
    vi.mocked(client.post).mockResolvedValue({ data: cluster });

    expect(await caller.duplicate()).toEqual(cluster);
    expect(client.post).toHaveBeenCalledTimes(1);
    expect(client.post).toHaveBeenCalledWith(
      `/v1/studies/${studyId}/areas/${areaId}/thermals/${clusterId}`,
      null,
      { params: { newName: "Copy" } },
    );
  });

  test("sends bulk deletion IDs in the request body", async () => {
    vi.mocked(client.delete).mockResolvedValue({ data: null });

    expect(await caller.delete()).toBeUndefined();
    expect(client.delete).toHaveBeenCalledTimes(1);
    expect(client.delete).toHaveBeenCalledWith(listUrl, { data: [clusterId, "other"] });
  });

  test("propagates request failures to existing error handling", async () => {
    const error = new Error("Request failed");
    vi.mocked(client.get).mockRejectedValue(error);

    await expect(caller.list()).rejects.toBe(error);
  });
});

test("caches complete cluster properties so consumers can select without a detail request", async () => {
  const response = { ...cluster, ...versionedProperties, group: null };
  vi.mocked(client.get).mockResolvedValue({ data: [response] });

  const options = thermalQueries.list(studyId, areaId);
  await queryClient.fetchQuery(options);
  const selected = queryClient.getQueryData(options.queryKey)?.find(({ id }) => id === clusterId);

  expect(selected).toEqual({ ...response, id: clusterId });
  expect(client.get).toHaveBeenCalledTimes(1);
  expect(client.get).toHaveBeenCalledWith(listUrl);
});

test("adapts an absent group for legacy views without changing the API model", async () => {
  const response = { ...cluster, group: null };
  vi.mocked(client.get).mockResolvedValue({ data: response });

  expect(await api.getThermalCluster({ studyId, areaId, clusterId })).toEqual(response);
  expect(await legacy.getThermalCluster(studyId, areaId, clusterId)).toEqual({
    ...response,
    group: "",
  });
  expect(response.group).toBeNull();
});

test("rejects invalid create and update values before sending a request", async () => {
  await expect(
    api.createThermalCluster({
      studyId,
      areaId,
      values: { name: "New cluster", nominalCapacity: NaN },
    }),
  ).rejects.toBeInstanceOf(ZodError);
  await expect(
    api.updateThermalCluster({ studyId, areaId, clusterId, values: { nominalCapacity: NaN } }),
  ).rejects.toBeInstanceOf(ZodError);

  expect(client.post).not.toHaveBeenCalled();
  expect(client.patch).not.toHaveBeenCalled();
});

test("strips read-only fields from legacy update values and preserves nullable fields", async () => {
  vi.mocked(client.patch).mockResolvedValue({ data: cluster });

  await legacy.updateThermalCluster(studyId, areaId, clusterId, {
    id: clusterId,
    name: "Ignored name",
    so2: null,
    costGeneration: null,
    enabled: false,
  });

  expect(client.patch).toHaveBeenCalledWith(`${listUrl}/${clusterId}`, {
    so2: null,
    costGeneration: null,
    enabled: false,
  });
});
