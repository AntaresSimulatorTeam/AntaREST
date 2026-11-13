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
import { getWorkspaceDiskUsage } from "..";

vi.mock("@/services/api/client", () => ({
  default: { get: vi.fn() },
}));

const response = {
  total_bytes: 1000,
  used_bytes: 830,
  free_bytes: 150,
};

beforeEach(() => {
  vi.resetAllMocks();
});

test("encodes the workspace name and maps its byte counts", async () => {
  vi.mocked(client.get).mockResolvedValue({ data: response });

  const usage = await getWorkspaceDiskUsage("études_2026");

  expect(client.get).toHaveBeenCalledWith("/v1/filesystem/ws/%C3%A9tudes_2026");
  expect(usage).toEqual({ totalBytes: 1000, usedBytes: 830, freeBytes: 150 });
});

test("rejects the backend's all-zero unavailable response", async () => {
  vi.mocked(client.get).mockResolvedValue({
    data: { total_bytes: 0, used_bytes: 0, free_bytes: 0 },
  });

  await expect(getWorkspaceDiskUsage("default")).rejects.toBeInstanceOf(ZodError);
});
