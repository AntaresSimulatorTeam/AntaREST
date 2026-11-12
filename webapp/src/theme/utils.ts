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
 * Returns the MUI color for resource usage, with higher usage indicating less capacity.
 *
 * @param percentage - Resource usage as a percentage.
 * @returns Success through 50%, warning above 50%, or error from 90%.
 */
export function getUsageColor(percentage: number) {
  if (percentage >= 90) {
    return "error";
  }

  if (percentage > 50) {
    return "warning";
  }

  return "success";
}
