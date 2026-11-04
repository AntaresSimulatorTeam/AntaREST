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

export const RENEWABLE_GROUPS = [
  "wind onshore",
  "wind offshore",
  "solar thermal",
  "solar pv",
  "solar rooftop",
  "other res 1",
  "other res 2",
  "other res 3",
  "other res 4",
] as const;

export const TS_INTERPRETATION_OPTIONS = ["power-generation", "production-factor"] as const;
