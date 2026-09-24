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
import client from "@/services/api/client";
import { ZodError, type z } from "zod";
import * as api from "..";
import type { thermalClusterSchema } from "../schemas";

vi.mock("@/services/api/client", () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

const studyId = "study-1";
const areaId = "area-1";
const clusterId = "gas cluster";
const listUrl = `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`;
const cluster: z.input<typeof thermalClusterSchema> = {
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

beforeEach(() => {
  vi.resetAllMocks();
});

afterEach(() => {
  queryClient.clear();
});

test("caches complete cluster properties so consumers can select without a detail request", async () => {
  const response = {
    ...cluster,
    group: null,
    so2: null,
    nh3: 0,
    costGeneration: "useCostTimeseries",
    efficiency: 50,
    variableOMCost: 15,
  };
  vi.mocked(client.get).mockResolvedValue({ data: [response] });

  const options = thermalQueries.list(studyId, areaId);
  await queryClient.fetchQuery(options);
  const selected = queryClient.getQueryData(options.queryKey)?.find(({ id }) => id === clusterId);

  expect(selected).toEqual({ ...response, id: clusterId, so2: undefined });
  expect(client.get).toHaveBeenCalledTimes(1);
  expect(client.get).toHaveBeenCalledWith(listUrl);
});

test("rejects malformed list responses", async () => {
  vi.mocked(client.get).mockResolvedValue({
    data: [{ ...cluster, genTs: "unknown behavior" }],
  });

  await expect(api.getThermalClusters({ studyId, areaId })).rejects.toBeInstanceOf(ZodError);
});

test("creates a cluster from a name-only payload", async () => {
  vi.mocked(client.post).mockResolvedValue({ data: cluster });

  const created = await api.createThermalCluster({
    studyId,
    areaId,
    values: { name: "New cluster" },
  });

  expect(created).toEqual(cluster);
  expect(client.post).toHaveBeenCalledWith(listUrl, { name: "New cluster" });
});

test("patches only supplied values and normalizes absent response fields", async () => {
  const values = { enabled: false };
  const updated = { ...cluster, ...values, so2: null, costGeneration: null };
  vi.mocked(client.patch).mockResolvedValue({ data: updated });

  expect(await api.updateThermalCluster({ studyId, areaId, clusterId, values })).toEqual({
    ...updated,
    so2: undefined,
    costGeneration: undefined,
  });
  expect(client.patch).toHaveBeenCalledWith(`${listUrl}/${clusterId}`, values);
});

test("duplicates through the dedicated endpoint and newName query parameter", async () => {
  vi.mocked(client.post).mockResolvedValue({ data: cluster });

  await api.duplicateThermalCluster({ studyId, areaId, clusterId, newName: "Copy" });

  expect(client.post).toHaveBeenCalledWith(
    `/v1/studies/${studyId}/areas/${areaId}/thermals/${clusterId}`,
    null,
    { params: { newName: "Copy" } },
  );
});

test("sends bulk deletion IDs in the request body", async () => {
  await api.deleteThermalClusters({ studyId, areaId, clusterIds: [clusterId, "other"] });

  expect(client.delete).toHaveBeenCalledWith(listUrl, { data: [clusterId, "other"] });
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
