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
import { renewableQueries } from "@/queries/renewables/queries";
import client from "@/services/api/client";
import { ZodError, type z } from "zod";
import * as api from "..";
import type { renewableClusterSchema } from "../schemas";

vi.mock("@/services/api/client", () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

const studyId = "study-1";
const areaId = "area-1";
const clusterId = "wind cluster";
const listUrl = `/v1/studies/${studyId}/areas/${areaId}/clusters/renewable`;
const cluster: z.input<typeof renewableClusterSchema> = {
  id: "Wind Cluster",
  name: "Wind Cluster",
  group: "custom wind",
  tsInterpretation: "production-factor",
  enabled: true,
  unitCount: 2,
  nominalCapacity: 100,
};

beforeEach(() => {
  vi.resetAllMocks();
});

afterEach(() => {
  queryClient.clear();
});

test("caches complete cluster properties separately for each study and area", async () => {
  const ungroupedCluster = { ...cluster, id: "Ungrouped", name: "Ungrouped", group: null };
  vi.mocked(client.get).mockResolvedValue({ data: [cluster, ungroupedCluster] });

  const options = renewableQueries.list(studyId, areaId);
  await queryClient.fetchQuery(options);
  const cached = queryClient.getQueryData(options.queryKey);

  expect(cached?.find(({ id }) => id === clusterId)).toEqual({ ...cluster, id: clusterId });
  expect(cached?.find(({ id }) => id === "ungrouped")).toEqual({
    ...ungroupedCluster,
    id: "ungrouped",
  });
  expect(
    queryClient.getQueryData(renewableQueries.list("other-study", areaId).queryKey),
  ).toBeUndefined();
  expect(
    queryClient.getQueryData(renewableQueries.list(studyId, "other-area").queryKey),
  ).toBeUndefined();
  expect(options.staleTime).toBe(0);
  expect(client.get).toHaveBeenCalledTimes(1);
  expect(client.get).toHaveBeenCalledWith(listUrl);
});

test("rejects malformed list responses", async () => {
  vi.mocked(client.get).mockResolvedValue({
    data: [{ ...cluster, tsInterpretation: "unknown interpretation" }],
  });

  await expect(api.getRenewableClusters({ studyId, areaId })).rejects.toBeInstanceOf(ZodError);
});

test("creates a cluster from a name-only payload", async () => {
  vi.mocked(client.post).mockResolvedValue({ data: cluster });

  const created = await api.createRenewableCluster({
    studyId,
    areaId,
    values: { name: "New cluster" },
  });

  expect(created).toEqual(cluster);
  expect(client.post).toHaveBeenCalledWith(listUrl, { name: "New cluster" });
});

test("patches supplied values while omitting null writes and preserving null response groups", async () => {
  const updated = { ...cluster, enabled: false, nominalCapacity: 0, group: null };
  vi.mocked(client.patch).mockResolvedValue({ data: updated });

  const result = await api.updateRenewableCluster({
    studyId,
    areaId,
    clusterId,
    values: { enabled: false, nominalCapacity: 0, group: null, unitCount: null },
  });

  expect(result).toEqual(updated);
  const [url, body] = vi.mocked(client.patch).mock.calls[0];
  expect(url).toBe(`${listUrl}/${clusterId}`);
  expect(JSON.parse(JSON.stringify(body))).toEqual({ enabled: false, nominalCapacity: 0 });
});

test("duplicates through the dedicated endpoint and newName query parameter", async () => {
  vi.mocked(client.post).mockResolvedValue({ data: cluster });

  await api.duplicateRenewableCluster({ studyId, areaId, clusterId, newName: "Copy" });

  expect(client.post).toHaveBeenCalledWith(
    `/v1/studies/${studyId}/areas/${areaId}/renewables/${clusterId}`,
    null,
    { params: { newName: "Copy" } },
  );
});

test("sends bulk deletion IDs in the request body", async () => {
  await api.deleteRenewableClusters({ studyId, areaId, clusterIds: [clusterId, "other"] });

  expect(client.delete).toHaveBeenCalledWith(listUrl, { data: [clusterId, "other"] });
});

test("rejects invalid create and update values before sending a request", async () => {
  await expect(
    api.createRenewableCluster({ studyId, areaId, values: { name: "New cluster", unitCount: 0 } }),
  ).rejects.toBeInstanceOf(ZodError);
  await expect(
    api.updateRenewableCluster({ studyId, areaId, clusterId, values: { nominalCapacity: -1 } }),
  ).rejects.toBeInstanceOf(ZodError);

  expect(client.post).not.toHaveBeenCalled();
  expect(client.patch).not.toHaveBeenCalled();
});
