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

import client from "@/services/api/client";
import { ZodError } from "zod";
import * as api from "..";
import { storageCreationSchema, storageUpdateSchema } from "../schemas";
import type { StorageResponse } from "../types";

vi.mock("@/services/api/client", () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

const studyId = "study-1";
const areaId = "area-1";
const storageId = "Battery A";
const params = { studyId, areaId, storageId };
const listUrl = `/v1/studies/${studyId}/areas/${areaId}/storages`;
const storage: StorageResponse = {
  id: storageId,
  name: "Battery A",
  group: "custom battery",
  injectionNominalCapacity: 100,
  withdrawalNominalCapacity: 90,
  reservoirCapacity: 500,
  efficiency: 0.9,
  initialLevel: 0.5,
  initialLevelOptim: true,
  enabled: true,
  efficiencyWithdrawal: 1.1,
  penalizeVariationInjection: true,
  penalizeVariationWithdrawal: false,
  allowOverflow: true,
};

beforeEach(() => {
  vi.resetAllMocks();
});

test("returns complete list and detail properties with unchanged server IDs", async () => {
  vi.mocked(client.get)
    .mockResolvedValueOnce({ data: [storage] })
    .mockResolvedValueOnce({ data: storage });

  expect(await api.getStorages(params)).toEqual([storage]);
  expect(await api.getStorage(params)).toEqual(storage);
  expect(client.get).toHaveBeenNthCalledWith(1, listUrl);
  expect(client.get).toHaveBeenNthCalledWith(2, `${listUrl}/${storageId}`);
});

test.each(["battery", "custom group", "", null])(
  "preserves the response group %s",
  async (group) => {
    vi.mocked(client.get).mockResolvedValue({ data: { ...storage, group } });
    expect(await api.getStorage(params)).toEqual({ ...storage, group });
  },
);

test.each([null, undefined])(
  "normalizes absent version-specific fields (%s) without UI defaults",
  async (absent) => {
    const data = {
      ...storage,
      enabled: absent,
      efficiencyWithdrawal: absent,
      penalizeVariationInjection: absent,
      penalizeVariationWithdrawal: absent,
      allowOverflow: absent,
    };
    vi.mocked(client.get).mockResolvedValue({ data: JSON.parse(JSON.stringify(data)) });

    expect(await api.getStorage(params)).toEqual({
      ...storage,
      enabled: undefined,
      efficiencyWithdrawal: undefined,
      penalizeVariationInjection: undefined,
      penalizeVariationWithdrawal: undefined,
      allowOverflow: undefined,
    });
  },
);

test.each([
  { ...storage, reservoirCapacity: "500" },
  { ...storage, group: 1 },
  { ...storage, initialLevel: 2 },
  { ...storage, enabled: "true" },
  { ...storage, name: undefined },
])("rejects malformed list and detail responses", async (data) => {
  vi.mocked(client.get)
    .mockResolvedValueOnce({ data: [data] })
    .mockResolvedValueOnce({ data });

  await expect(api.getStorages(params)).rejects.toBeInstanceOf(ZodError);
  await expect(api.getStorage(params)).rejects.toBeInstanceOf(ZodError);
});

test("creates from a name-only payload and validates the response", async () => {
  vi.mocked(client.post).mockResolvedValue({ data: storage });

  expect(await api.createStorage({ studyId, areaId, values: { name: storage.name } })).toEqual(
    storage,
  );
  expect(client.post).toHaveBeenCalledWith(listUrl, { name: storage.name });
});

test("updates only supplied fields and retains zero, false and an explicit empty group", async () => {
  vi.mocked(client.patch).mockResolvedValue({ data: { ...storage, group: null } });

  const result = await api.updateStorage({
    ...params,
    values: {
      enabled: false,
      initialLevel: 0,
      group: "",
    },
  });

  const [url, body] = vi.mocked(client.patch).mock.calls[0];
  expect(url).toBe(`${listUrl}/${storageId}`);
  expect(JSON.parse(JSON.stringify(body))).toEqual({ enabled: false, initialLevel: 0, group: "" });
  expect(result.group).toBeNull();
});

test("accepts omitted fields but rejects null for non-nullable creation and update fields", () => {
  expect(storageUpdateSchema.parse({})).toEqual({});
  expect(storageUpdateSchema.safeParse({ efficiency: null }).success).toBe(false);
  expect(storageCreationSchema.safeParse({ name: "New", efficiency: null }).success).toBe(false);
});

test("strips identifiers and ignored names from write bodies without mutating the input", async () => {
  vi.mocked(client.post).mockResolvedValue({ data: storage });
  vi.mocked(client.patch).mockResolvedValue({ data: storage });
  const values = { ...storage, name: "New name", group: null };

  await api.createStorage({ studyId, areaId, values });
  await api.updateStorage({ ...params, values });

  expect(vi.mocked(client.post).mock.calls[0][1]).not.toHaveProperty("id");
  expect(vi.mocked(client.post).mock.calls[0][1]).toHaveProperty("name", "New name");
  expect(vi.mocked(client.patch).mock.calls[0][1]).not.toHaveProperty("id");
  expect(vi.mocked(client.patch).mock.calls[0][1]).not.toHaveProperty("name");
  expect(vi.mocked(client.patch).mock.calls[0][1]).toHaveProperty("group", null);
  expect(values).toEqual({ ...storage, name: "New name", group: null });
});

test.each([
  { injectionNominalCapacity: -1 },
  { withdrawalNominalCapacity: -1 },
  { reservoirCapacity: -1 },
  { efficiency: -1 },
  { efficiencyWithdrawal: -1 },
  { initialLevel: -0.1 },
  { initialLevel: 1.1 },
])("rejects invalid creation and update values before sending HTTP requests", async (values) => {
  await expect(
    api.createStorage({ studyId, areaId, values: { name: "New", ...values } }),
  ).rejects.toBeInstanceOf(ZodError);
  await expect(api.updateStorage({ ...params, values })).rejects.toBeInstanceOf(ZodError);
  expect(client.post).not.toHaveBeenCalled();
  expect(client.patch).not.toHaveBeenCalled();
});

test("requires a name for creation and accepts efficiencies above one for newer studies", () => {
  expect(storageCreationSchema.safeParse({}).success).toBe(false);
  expect(
    storageCreationSchema.parse({ name: "New", efficiency: 1.1, efficiencyWithdrawal: 1.2 }),
  ).toMatchObject({ efficiency: 1.1, efficiencyWithdrawal: 1.2 });
});

test("validates create, update and duplicate responses", async () => {
  vi.mocked(client.post).mockResolvedValue({ data: { ...storage, reservoirCapacity: "invalid" } });
  vi.mocked(client.patch).mockResolvedValue({ data: { ...storage, initialLevel: null } });

  await expect(
    api.createStorage({ studyId, areaId, values: { name: "New" } }),
  ).rejects.toBeInstanceOf(ZodError);
  await expect(api.updateStorage({ ...params, values: { enabled: false } })).rejects.toBeInstanceOf(
    ZodError,
  );
  await expect(api.duplicateStorage({ ...params, newName: "Copy" })).rejects.toBeInstanceOf(
    ZodError,
  );
});

test("duplicates with a query parameter and deletes a list of IDs in the body", async () => {
  vi.mocked(client.post).mockResolvedValue({ data: storage });

  expect(await api.duplicateStorage({ ...params, newName: "Copy" })).toEqual(storage);
  await api.deleteStorages({ studyId, areaId, storageIds: [storageId, "other"] });

  expect(client.post).toHaveBeenCalledWith(`${listUrl}/${storageId}`, null, {
    params: { newName: "Copy" },
  });
  expect(client.delete).toHaveBeenCalledWith(listUrl, { data: [storageId, "other"] });
});
