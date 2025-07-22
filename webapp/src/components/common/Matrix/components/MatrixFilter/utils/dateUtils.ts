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

import type { TFunction } from "i18next";
import {
  createLocalizedTemporalLabels,
  getTemporalRange,
  type TimeIndexingType,
} from "@/utils/date/matrixDateUtils";
import type { LocalizedTimeLabel, TemporalRange } from "../types";

/**
 * Gets the default min and max values for a given indexing type
 *
 * @param indexingType - The type of temporal index (day, month, etc.)
 * @returns An object with the min and max values
 */
export function getDefaultRangeForIndexType(indexingType: TimeIndexingType): TemporalRange {
  return getTemporalRange(indexingType);
}

/**
 * Creates localized arrays of months or weekdays for UI components
 *
 * @param type - Either "month" or "weekday"
 * @param t - The translation function from useTranslation()
 * @returns Array of objects with value, label, and shortLabel properties
 */
export function getLocalizedTimeLabels(
  type: "month" | "weekday",
  t: TFunction,
): LocalizedTimeLabel[] {
  return createLocalizedTemporalLabels(type, t);
}
