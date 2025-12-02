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

export const VARIABLE_VIEW_FREQUENCIES = [
  "hourly",
  "daily",
  "weekly",
  "monthly",
  "annual",
] as const;

export const VARIABLE_VIEW_OBJECT_TYPES = [
  "area",
  "link",
  "thermal_cluster",
  "renewable_cluster",
  "short_term_storage",
] as const;

export const VARIABLE_VIEW_EXPORT_FORMATS = ["json", "csv", "tsv"] as const;

export const MONTE_CARLO_MODES = ["mc-ind", "mc-all", "variable-per-variable"] as const;
