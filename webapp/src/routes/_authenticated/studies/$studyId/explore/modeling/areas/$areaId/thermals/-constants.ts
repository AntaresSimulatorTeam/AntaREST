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

import type { ThermalCluster } from "@/services/api/studies/areas/thermals/types";

/** Order of the emission fields displayed in the parameters form. */
export const THERMAL_POLLUTANTS = [
  "so2",
  "nh3",
  "nox",
  "nmvoc",
  "pm25",
  "pm5",
  "pm10",
  "op1",
  "op2",
  "op3",
  "op4",
  "op5",
] as const satisfies ReadonlyArray<keyof ThermalCluster>;

export const COMMON_MATRIX_COLS = [
  "Marginal cost modulation",
  "Market bid modulation",
  "Capacity modulation",
  "Min gen modulation",
] as const;

export const TS_GEN_MATRIX_COLS = [
  "FO Duration",
  "PO Duration",
  "FO Rate",
  "PO Rate",
  "NPO Min",
  "NPO Max",
] as const;
