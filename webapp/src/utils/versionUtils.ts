/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import semver from "semver";
import { isNumericValue } from "./numberUtils";

export const ZERO_SEMVER = "0.0.0" as const;

// The maximum value for any semver component is `Number.MAX_SAFE_INTEGER`
export const MAX_SEMVER =
  `${Number.MAX_SAFE_INTEGER}.${Number.MAX_SAFE_INTEGER}.${Number.MAX_SAFE_INTEGER}` as const;

/**
 * Normalizes a version value from the API into a full semantic version string (MAJOR.MINOR.PATCH).
 *
 * Supported input formats:
 * - 3-digit numeric (e.g. 930 or "930")  -> "9.3.0"
 * - Partial string (e.g. "9.3" -> "9.3.0", "9" -> "9.0.0")
 * - Any string accepted by `semver.coerce()`
 *
 * This normalization ensures the result can be safely used with semver library.
 *
 * @param version - Version as number or string.
 * @returns A semantic version string, or "0.0.0" on failure.
 */
export function toSemanticVersion(version: number | string) {
  const numberVerStr = version.toString();

  // e.g., 930 or "930" -> "9.3.0"
  if (numberVerStr.length === 3 && numberVerStr.split("").every(isNumericValue)) {
    return `${numberVerStr[0]}.${numberVerStr[1]}.${numberVerStr[2]}`;
  }

  // e.g., "9.3" -> "9.3.0" or "9" -> "9.0.0"
  return semver.valid(semver.coerce(version)) || ZERO_SEMVER;
}

/**
 * Converts a semantic version string into a numeric representation used by certain API endpoints.
 *
 * Uses the same algorithm as `_TripletVersion.__int__()` in `study_version.py`.
 *
 * @param version - Semantic version string.
 * @returns A numeric representation of the version, or `NaN` if invalid.
 */
export function toNumberVersion(version: string) {
  const parsed = semver.parse(version);

  if (!parsed) {
    return NaN;
  }

  //
  return parsed.major * 100 + parsed.minor * 10 + parsed.patch;
}

/**
 * Compacts a semantic version string by removing trailing zeros.
 *
 * The API represents versions in a compact form, omitting unnecessary ".0" components.
 *
 * Examples:
 * - "1.0.0" -> "1"
 * - "1.2.0" -> "1.2"
 * - "1.2.3" -> "1.2.3"
 *
 * @param version - Semantic version string.
 * @returns A compacted version string, or the original input if invalid.
 */
export function compactSemanticVersion(version: string) {
  const parsed = semver.parse(version);
  if (!parsed) {
    return version;
  }

  const { major, minor, patch } = parsed;

  // Case: x.0.0 -> "x"
  if (minor === 0 && patch === 0) {
    return `${major}`;
  }

  // Case: x.y.0 -> "x.y"
  if (patch === 0) {
    return `${major}.${minor}`;
  }

  // Case: x.y.z -> unchanged
  return `${major}.${minor}.${patch}`;
}

/**
 * Gets the highest semantic version from a list of version strings.
 *
 * @param versions - Array of semantic version strings.
 * @returns The highest version string, or `null` if the list is empty.
 */
export function getHighestVersion(versions: string[]) {
  if (versions.length === 0) {
    return null;
  }

  // `semver.rsort()` mutates the input array, so we create a copy
  const sortedVersions = semver.rsort([...versions]);

  return sortedVersions[0];
}

/**
 * Generates version options suitable for UI components from a list of semantic version strings.
 * Each option includes the original version string as `value` and a compacted version as `label`.
 *
 * @param versions - Array of semantic version strings.
 * @returns Array of version options with `value` and `label`.
 */
export function getSemanticVersionOptions(versions: string[]) {
  return versions.map((version) => ({
    value: version,
    label: compactSemanticVersion(version),
  }));
}
