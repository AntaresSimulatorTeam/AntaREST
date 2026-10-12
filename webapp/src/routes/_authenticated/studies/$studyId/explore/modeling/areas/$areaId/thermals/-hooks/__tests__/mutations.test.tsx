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
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import type { QueryClient } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import useCreateThermal from "../useCreateThermal";
import useDeleteThermals from "../useDeleteThermals";
import useDuplicateThermal from "../useDuplicateThermal";
import useThermals from "../useThermals";
import { cluster } from "./fixtures";

const scope = { studyId: "study", areaId: "area" };
const key = thermalKeys.list(scope.studyId, scope.areaId);
let client: QueryClient;
let wrapper: ReturnType<typeof createQueryWrapper>;

beforeEach(() => {
  client = createQueryClient();
  wrapper = createQueryWrapper(client);
  client.setQueryData(key, [cluster]);

  vi.mocked(api.getThermals).mockReset().mockResolvedValue([cluster]);
  vi.mocked(api.createThermal).mockReset().mockResolvedValue(cluster);
  vi.mocked(api.deleteThermals).mockReset().mockResolvedValue(undefined);
  vi.mocked(api.duplicateThermal).mockReset().mockResolvedValue(cluster);
});

afterEach(() => client.clear());

describe("Thermal mutations", () => {
  test("deleting a cluster updates its list and invalidates dependent reserves", async () => {
    const coal = { ...cluster, id: "coal", name: "Coal" };
    client.setQueryData(key, [cluster, coal]);

    const affected = [
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

    const { result } = renderHook(
      () => {
        useThermals(scope);
        return useDeleteThermals(scope);
      },
      { wrapper },
    );

    await act(async () => {
      await result.current.mutateAsync({ ...scope, thermalIds: [cluster.id] });
    });

    expect(client.getQueryData(key)).toEqual([coal]);
    expect(api.getThermals).not.toHaveBeenCalled();

    affected.forEach((key) => {
      expect(client.getQueryState(key)?.isInvalidated).toBe(true);
    });
    untouched.forEach((key) => {
      expect(client.getQueryState(key)?.isInvalidated).toBe(false);
    });
  });

  test("creating and duplicating clusters updates the list without refetching", async () => {
    const created = { ...cluster, id: "coal", name: "Coal" };
    const duplicated = { ...cluster, id: "gas copy", name: "Gas Copy" };
    vi.mocked(api.createThermal).mockResolvedValue(created);
    vi.mocked(api.duplicateThermal).mockResolvedValue(duplicated);

    const { result } = renderHook(
      () => ({
        list: useThermals(scope),
        create: useCreateThermal(scope),
        duplicate: useDuplicateThermal(scope),
      }),
      { wrapper },
    );

    await act(async () => {
      await expect(
        result.current.create.mutateAsync({ ...scope, values: { name: created.name } }),
      ).resolves.toEqual(created);
    });

    await waitFor(() => expect(result.current.list.data).toHaveLength(2));
    expect(client.getQueryData(key)).toEqual([cluster, created]);

    await act(async () => {
      await result.current.duplicate.mutateAsync({
        ...scope,
        thermalId: cluster.id,
        newName: duplicated.name,
      });
    });

    await waitFor(() => expect(result.current.list.data).toHaveLength(3));
    expect(client.getQueryData(key)).toEqual([cluster, created, duplicated]);
    expect(api.getThermals).not.toHaveBeenCalled();
  });
});
