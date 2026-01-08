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

import debug from "debug";
import semver from "semver";

const log = debug("antares:utils:versionUtils");

export const ZERO_SEMVER = "0.0.0" as const;

// The maximum value for any semver component is `Number.MAX_SAFE_INTEGER`
export const MAX_SEMVER =
  `${Number.MAX_SAFE_INTEGER}.${Number.MAX_SAFE_INTEGER}.${Number.MAX_SAFE_INTEGER}` as const;

/**
 * Normalizes a version value from the API into a full semantic version string (MAJOR.MINOR.PATCH).
 *
 * Supported input formats:
 * - Number, e.g. 9 -> "9.0.0", 930 -> "9.3.0", 1011 -> "10.1.1"
 * - Partial string, e.g. "9.3" -> "9.3.0", "9" -> "9.0.0")
 * - Any string accepted by `semver.coerce()`
 *
 * This normalization ensures the result can be safely used with semver library.
 *
 * @param version - Version as number or string.
 * @returns A semantic version string, or "0.0.0" on failure.
 */
export function toSemanticVersion(version: number | string) {
  if (typeof version === "number") {
    // Uses the same algorithm as `_TripletVersion.parse(int)` in `study_version.py`.
    if (Number.isInteger(version)) {
      if (version >= 0 && version < 100) {
        return `${version}.0.0`;
      }

      if (version >= 100) {
        const major = Math.floor(version / 100);
        const remainderAfterMajor = version % 100;
        const minor = Math.floor(remainderAfterMajor / 10);
        const patch = remainderAfterMajor % 10;

        const ver = `${major}.${minor}.${patch}`;

        // Check if the maximum semver component value is not exceeded
        if (semver.valid(ver)) {
          return ver;
        }
      }
    }

    log("toSemanticVersion(): invalid number version value '%d'", version);
    return ZERO_SEMVER;
  }

  const ver = semver.valid(semver.coerce(version));

  // e.g., "9.3" -> "9.3.0" or "9" -> "9.0.0"
  if (ver === null) {
    log("toSemanticVersion(): invalid string version value '%s'", version);
    return ZERO_SEMVER;
  }

  return ver;
}

/**
 * Compacts a semantic version string by removing trailing zeros.
 *
 * The API represents versions in a compact form, omitting unnecessary ".0" components.
 *
 * If the input is an invalid semantic version, the original input is returned.
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
    log("compactSemanticVersion(): invalid semantic version '%s'", version);
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
 * If the list is empty or contains invalid semantic version(s), returns `null`.
 *
 * @param versions - Array of semantic version strings.
 * @returns The highest version string, or `null` if input is invalid.
 */
export function getHighestVersion(versions: string[]) {
  if (versions.length === 0) {
    return null;
  }

  try {
    // `semver.rsort()` mutates the input array, so we create a copy
    const sortedVersions = semver.rsort([...versions]);
    return sortedVersions[0];
  } catch {
    log("getHighestVersion(): invalid semantic version in list %o", versions);
    return null;
  }
}

/**
 * Generates version options suitable for UI components from a list of semantic version strings.
 * Each option includes the original version string as `value` and a compacted version as `label`.
 *
 * Filters out any occurrence of `ZERO_SEMVER` and invalid semantic versions.
 *
 * @param versions - Array of semantic version strings.
 * @returns Array of version options with `value` and `label`.
 */
export function getSemanticVersionOptions(versions: string[]) {
  return versions
    .filter((v) => v !== ZERO_SEMVER && semver.valid(v))
    .map((version) => ({
      value: version,
      label: compactSemanticVersion(version),
    }));
}
