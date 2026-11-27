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

import { getGemsViews, materializeGemsViews } from "@/services/api/studies/outputs/gemsViews";
import type { GemsViewsState } from "@/services/api/studies/outputs/gemsViews/types";
import { getTask } from "@/services/api/tasks";
import { TaskStatus } from "@/services/api/tasks/constants";
import { taskSchema } from "@/services/api/tasks/schemas";
import { createQueryClient, createQueryWrapper, deferred } from "@/tests/queryUtils";
import { MutationObserver, useQuery } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { taskQueries } from "../../tasks/queries";
import { outputMutations } from "../mutations";
import { outputQueries } from "../queries";
import useGemsViewsMaterializationTask from "../useGemsViewsMaterializationTask";

vi.mock("@/services/api/client", () => ({ default: {} }));
vi.mock("@/services/api/studies/outputs/gemsViews");
vi.mock("@/services/api/tasks");

const output = { studyId: "study", outputId: "output" };
const metadata = outputQueries.gemsViews(output);
const ready: GemsViewsState = { status: "READY", views: [] };
const completedTask = taskSchema.parse({
  id: "task",
  name: "Prepare views",
  creationDateUtc: "2026-01-01",
  status: TaskStatus.Completed,
});
const inProgress: GemsViewsState = { status: "IN_PROGRESS", taskId: completedTask.id };
const client = createQueryClient();
const wrapper = createQueryWrapper(client);

function startPreparation() {
  return new MutationObserver(client, outputMutations.materializeGemsViews(output)).mutate();
}

function observeViews() {
  return renderHook(
    () => {
      const { data } = useQuery(metadata);
      useGemsViewsMaterializationTask(output, data);
      return data;
    },
    { wrapper },
  );
}

afterEach(() => client.clear());

test("a repeat preparation response preserves the completion refetch and ready views", async () => {
  const refresh = deferred<GemsViewsState>();
  const repeat = deferred<string>();
  vi.mocked(getGemsViews)
    .mockResolvedValueOnce({ status: "NOT_FOUND" })
    .mockReturnValueOnce(refresh.promise);
  vi.mocked(materializeGemsViews)
    .mockResolvedValueOnce(completedTask.id)
    .mockReturnValueOnce(repeat.promise)
    .mockResolvedValueOnce(completedTask.id);
  vi.mocked(getTask).mockResolvedValue(completedTask);
  const { result } = observeViews();
  await waitFor(() => expect(result.current?.status).toBe("NOT_FOUND"));

  await startPreparation();
  const pendingRepeat = startPreparation();
  await waitFor(() =>
    expect(client.getQueryState(metadata.queryKey)?.fetchStatus).toBe("fetching"),
  );
  expect(client.getQueryData(metadata.queryKey)).toEqual(inProgress);

  repeat.resolve(completedTask.id);
  await pendingRepeat;
  refresh.resolve(ready);

  await waitFor(() => expect(result.current).toEqual(ready));

  await startPreparation();

  expect(client.getQueryData(metadata.queryKey)).toEqual(ready);
});

test("refreshes late in-progress metadata when its task has already finished", async () => {
  const firstRead = deferred<GemsViewsState>();
  client.setQueryData(taskQueries.detail(completedTask.id).queryKey, completedTask);
  vi.mocked(getTask).mockResolvedValue(completedTask);
  vi.mocked(getGemsViews).mockReturnValueOnce(firstRead.promise).mockResolvedValueOnce(ready);
  const { result } = observeViews();

  firstRead.resolve(inProgress);

  await waitFor(() => expect(result.current).toEqual(ready));
});

test("refetches the views when the backend reports they are already prepared", async () => {
  vi.mocked(getGemsViews)
    .mockResolvedValueOnce({ status: "NOT_FOUND" })
    .mockResolvedValueOnce(ready);
  vi.mocked(materializeGemsViews).mockResolvedValue(undefined);
  const { result } = observeViews();
  await waitFor(() => expect(result.current?.status).toBe("NOT_FOUND"));

  await startPreparation();

  expect(client.getQueryData(metadata.queryKey)).toEqual(ready);
});
