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

/**
 * Sanitizes JSON response containing invalid "NaN" and "Infinity" literals.
 *
 * The backend serializes "NaN" and "Infinity" as literal tokens (e.g., {"value": "NaN"})
 * using Pydantic's ser_json_inf_nan="constants" configuration.
 * This is invalid JSON and causes JSON.parse() to fail.
 *
 * This function converts these literals to valid JSON strings before parsing.
 *
 * @param response - Raw response data from API (string or already parsed object).
 *
 * @returns Properly parsed JSON object with "NaN" and "Infinity" as strings,
 * or the original response if already parsed.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function sanitizeJsonResponse<T = unknown>(response: any): T {
  if (typeof response !== "string") {
    return response;
  }

  // Replace invalid JSON literals with valid JSON strings
  const sanitized = response.replace(/NaN/g, '"NaN"').replace(/Infinity/g, '"Infinity"');

  return JSON.parse(sanitized);
}
