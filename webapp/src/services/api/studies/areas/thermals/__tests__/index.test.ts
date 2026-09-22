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

import * as legacy from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/-utils";
import client from "@/services/api/client";
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
