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

import { TimeSeriesType } from "@/services/api/studies/timeseries/constants";
import type {
  TimeSeriesTypeConfig,
  TimeSeriesTypeValue,
} from "@/services/api/studies/timeseries/types";

export type TimeSeriesConfigValues = Record<
  TimeSeriesTypeValue,
  TimeSeriesTypeConfig & { enable: boolean }
>;

export const defaultValues = Object.values(TimeSeriesType).reduce((acc, type) => {
  acc[type] = { number: 1, enable: false };
  return acc;
}, {} as TimeSeriesConfigValues);
