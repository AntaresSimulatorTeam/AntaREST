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

export const THERMAL_GROUPS = [
  "gas",
  "hard coal",
  "lignite",
  "mixed fuel",
  "nuclear",
  "oil",
  "other 1",
  "other 2",
  "other 3",
  "other 4",
] as const;

export const TS_GENERATION_OPTIONS = [
  "use global",
  "force no generation",
  "force generation",
] as const;

export const TS_LAW_OPTIONS = ["geometric", "uniform"] as const;

export const COST_GENERATION_OPTIONS = ["SetManually", "useCostTimeseries"] as const;
