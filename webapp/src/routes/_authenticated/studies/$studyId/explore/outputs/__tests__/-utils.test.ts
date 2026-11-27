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
import { TaskStatus } from "@/services/api/tasks/constants";
import { createQueryClient } from "@/tests/queryUtils";
import { waitForOutputArchiveTask } from "../-utils";

vi.mock("@/services/api/client", () => ({ default: { get: vi.fn() } }));

const task = { id: "task-1", name: "Archive output", creationDateUtc: "2026-01-01" };
const result = { success: false, message: "Archive interrupted" };

test("recognizes an already completed archive without a WebSocket event", async () => {
  vi.mocked(client.get).mockResolvedValueOnce({ data: { ...task, status: TaskStatus.Completed } });

  await expect(waitForOutputArchiveTask(createQueryClient(), task.id)).resolves.toBeUndefined();
});

test("reports a running archive's eventual failure after a transient status read error", async () => {
  vi.useFakeTimers();

  try {
    vi.mocked(client.get)
      .mockResolvedValueOnce({ data: { ...task, status: TaskStatus.Running } })
      .mockRejectedValueOnce(new Error("Temporary connection failure"))
      .mockResolvedValueOnce({ data: { ...task, status: TaskStatus.Failed, result } });

    const completion = waitForOutputArchiveTask(createQueryClient(), task.id);

    await Promise.all([expect(completion).rejects.toThrow(result.message), vi.runAllTimersAsync()]);
  } finally {
    vi.useRealTimers();
  }
});

test.each([TaskStatus.Cancelled, TaskStatus.Timeout])(
  "reports the backend error for unsuccessful archive status %i",
  async (status) => {
    vi.mocked(client.get).mockResolvedValueOnce({ data: { ...task, status, result } });

    await expect(waitForOutputArchiveTask(createQueryClient(), task.id)).rejects.toThrow(
      result.message,
    );
  },
);
