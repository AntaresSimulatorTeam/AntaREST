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

// @vitest-environment node

import client from "@/services/api/client";
import { AxiosError } from "axios";
import { getFileContent } from "..";

vi.mock("@/services/api/client", () => ({ default: { get: vi.fn() } }));

async function getFileError(body: string) {
  const blob = new Blob([body], { type: "application/json; charset=utf-8" });
  const error = Object.assign(new AxiosError(), { response: { data: blob } });
  vi.mocked(client.get).mockRejectedValueOnce(error);

  await expect(getFileContent("/files", "report.txt")).rejects.toBe(error);

  return { blob, data: error.response.data };
}

test("decodes JSON error details from a blob", async () => {
  const details = { exception: "FileNotFound", description: "Missing file" };

  const { data } = await getFileError(JSON.stringify(details));

  expect(data).toEqual(details);
});

test("preserves the original blob when the JSON cannot be decoded", async () => {
  const { blob, data } = await getFileError("invalid JSON");

  expect(data).toBe(blob);
});
