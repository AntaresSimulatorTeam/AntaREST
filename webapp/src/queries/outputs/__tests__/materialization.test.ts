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
import { createQueryClient, createQueryWrapper } from "@/tests/queryUtils";
import { MutationObserver, useQuery } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { outputMutations } from "../mutations";
import { outputQueries } from "../queries";
import useGemsViewsMaterializationTask from "../useGemsViewsMaterializationTask";

vi.mock("@/services/api/client", () => ({ default: {} }));
vi.mock("@/services/api/studies/outputs/gemsViews");
vi.mock("@/services/api/tasks");

const output = { studyId: "study", outputId: "output" };
const metadata = outputQueries.gemsViews(output);
const ready: GemsViewsState = { status: "READY", views: [] };
const client = createQueryClient();
const wrapper = createQueryWrapper(client);

function startPreparation() {
  return new MutationObserver(client, outputMutations.materializeGemsViews(output)).mutate();
}

beforeEach(() => {
  vi.mocked(getGemsViews).mockResolvedValueOnce({ status: "NOT_FOUND" }).mockResolvedValue(ready);
  renderHook(() => useQuery(metadata), { wrapper });
});

afterEach(() => client.clear());

test("refreshes views after the task finishes and keeps them when a start returns a task ID", async () => {
  const taskId = "task";
  vi.mocked(materializeGemsViews).mockResolvedValue(taskId);
  vi.mocked(getTask).mockResolvedValue(
    taskSchema.parse({
      id: taskId,
      name: "Prepare views",
      creationDateUtc: "2026-01-01",
      status: TaskStatus.Completed,
    }),
  );

  await startPreparation();

  expect(client.getQueryData(metadata.queryKey)).toEqual({ status: "IN_PROGRESS", taskId });

  renderHook(() => useGemsViewsMaterializationTask(output, taskId), { wrapper });

  await waitFor(() => expect(client.getQueryData(metadata.queryKey)).toEqual(ready));

  await startPreparation();

  expect(client.getQueryData(metadata.queryKey)).toEqual(ready);
});

test("refetches the views when the backend reports they are already prepared", async () => {
  vi.mocked(materializeGemsViews).mockResolvedValue(undefined);

  await startPreparation();

  expect(client.getQueryData(metadata.queryKey)).toEqual(ready);
});
