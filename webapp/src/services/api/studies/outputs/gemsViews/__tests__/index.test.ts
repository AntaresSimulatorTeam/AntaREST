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
import { AxiosError } from "axios";
import { getGemsViews, materializeGemsViews } from "..";

vi.mock("@/services/api/client", () => ({ default: { get: vi.fn(), post: vi.fn() } }));

const output = { studyId: "study-1", outputId: "output-1" };
const views = [{ taxonomy: "balance", viewIds: {} }];

function httpError(status: number, data?: object) {
  return Object.assign(new AxiosError(`HTTP ${status}`), { response: { status, data } });
}

test.each([
  ["ready", { data: views }, { status: "READY", views }],
  [
    "in progress",
    httpError(404, { status: "IN_PROGRESS", task_id: "task-1" }),
    { status: "IN_PROGRESS", taskId: "task-1" },
  ],
  ["not prepared", httpError(404, { status: "NOT_FOUND", task_id: null }), { status: "NOT_FOUND" }],
  ["plain 404", httpError(404, { exception: "OutputGemsViewsNotFound" }), undefined],
] as const)("reads GEMS views: %s", async (_case, response, expected) => {
  if (response instanceof AxiosError) {
    vi.mocked(client.get).mockRejectedValueOnce(response);
  } else {
    vi.mocked(client.get).mockResolvedValueOnce(response);
  }

  let thrown: Error | undefined;
  const result = await getGemsViews(output).catch((error: Error) => {
    thrown = error;
  });

  expect(thrown).toBe(expected === undefined ? response : undefined);
  expect(result).toEqual(expected);
});

test("returns no task ID when the views are already prepared", async () => {
  vi.mocked(client.post).mockRejectedValueOnce(httpError(417));

  await expect(materializeGemsViews(output)).resolves.toBeUndefined();
});
