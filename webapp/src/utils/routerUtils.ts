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

import type { StorageMode, StudyMetadata } from "@/types/types";
import semver from "semver";
import { compactSemanticVersion } from "./versionUtils";

interface CheckRouteAvailabilityParams {
  study: StudyMetadata;
  minVersion: string;
  requiredStorageMode?: StorageMode;
  routePath: string;
}

/**
 * Checks if a route is available for a given study version or/and storage mode.
 *
 * Note: Replace with `beforeLoad` in route definition when Redux will be replaced by TanStack Query.
 *
 * @param params - The parameters for the check.
 * @param params.study - The study.
 * @param params.minVersion - The minimum required version for the route.
 * @param params.requiredStorageMode - The required storage mode for the route.
 * @param params.routePath - The path of the route being checked.
 *
 * @throws Will throw an error if the route is not available for the given study version.
 */
export function checkRouteAvailability({
  study,
  minVersion,
  requiredStorageMode,
  routePath,
}: CheckRouteAvailabilityParams) {
  if (minVersion && semver.lt(study.version, minVersion)) {
    throw new Error(
      `${routePath} is only available for study version ${compactSemanticVersion(minVersion)} and above.`,
    );
  }

  if (requiredStorageMode && study.storageMode !== requiredStorageMode) {
    throw new Error(
      `${routePath} is only available for studies with ${requiredStorageMode} storage mode.`,
    );
  }
}
