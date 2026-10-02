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

const NAN_LITERAL = "NaN";
const INFINITY_LITERAL = "Infinity";
const NEGATIVE_INFINITY_LITERAL = "-Infinity";

/**
 * Sanitizes JSON responses containing invalid NaN/Infinity literals.
 *
 * The backend can serialize NaN/Infinity as bare tokens (e.g. {"value": NaN}) when using
 * Pydantic's ser_json_inf_nan="constants" configuration.
 * These tokens are not valid JSON and cause JSON.parse() to fail.
 *
 * This function rewrites only occurrences that are outside JSON strings.
 *
 * @param response - Raw response data from API (string or already parsed object).
 * @returns Parsed JSON with NaN/Infinity represented as strings ("NaN", "Infinity", "-Infinity").
 */
export function sanitizeJsonResponse<T = unknown>(response: unknown): T {
  if (typeof response !== "string") {
    return response as T;
  }

  let inString = false;
  let escaped = false;
  let sanitized = "";

  for (let i = 0; i < response.length; i += 1) {
    const char = response[i];

    if (inString) {
      sanitized += char;
      if (escaped) {
        escaped = false;
      } else if (char === "\\") {
        escaped = true;
      } else if (char === '"') {
        inString = false;
      }
      continue;
    }

    if (char === '"') {
      inString = true;
      sanitized += char;
      continue;
    }

    if (response.startsWith(NEGATIVE_INFINITY_LITERAL, i)) {
      sanitized += `"${NEGATIVE_INFINITY_LITERAL}"`;
      i += NEGATIVE_INFINITY_LITERAL.length - 1;
      continue;
    }

    if (response.startsWith(INFINITY_LITERAL, i)) {
      sanitized += `"${INFINITY_LITERAL}"`;
      i += INFINITY_LITERAL.length - 1;
      continue;
    }

    if (response.startsWith(NAN_LITERAL, i)) {
      sanitized += `"${NAN_LITERAL}"`;
      i += NAN_LITERAL.length - 1;
      continue;
    }

    sanitized += char;
  }

  return JSON.parse(sanitized) as T;
}
