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
import { compactSemanticVersion } from "./versionUtils";

/**
 * Checks if a route is available for a given study version.
 *
 * Note: Replace with `beforeLoad` in route definition when Redux will be replaced by TanStack Query.
 *
 * @param params - The parameters for the check.
 * @param params.studyVersion - The version of the study.
 * @param params.minVersion - The minimum required version for the route.
 * @param params.routePath - The path of the route being checked.
 *
 * @throws Will throw an error if the route is not available for the given study version.
 */
export function checkRouteAvailability(params: {
  studyVersion: string;
  minVersion: string;
  routePath: string;
}) {
  const { studyVersion, minVersion, routePath } = params;

  if (semver.lt(studyVersion, minVersion)) {
    throw new Error(
      `${routePath} is only available for study version ${compactSemanticVersion(minVersion)} and above.`,
    );
  }
}
