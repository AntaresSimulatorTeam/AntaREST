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

import { getDayOfYear, getHours } from "date-fns";

/**
 * Get week number from day of year
 *
 * @param dayOfYear - Day of year (1-366)
 * @returns Week number (1-53)
 */
export function getWeekFromDayOfYear(dayOfYear: number): number {
  return Math.ceil(dayOfYear / 7);
}

/**
 * Get hour of year from date
 *
 * @param date - The date
 * @returns Hour of year (1-8760)
 */
export function getHourOfYear(date: Date): number {
  return (getDayOfYear(date) - 1) * 24 + getHours(date) + 1;
}
