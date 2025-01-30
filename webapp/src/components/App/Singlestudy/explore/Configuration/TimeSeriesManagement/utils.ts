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

import { TSType } from "@/services/api/studies/timeseries/constants";
import type { TSTypeConfig, TSConfigDTO, TTSType } from "@/services/api/studies/timeseries/types";

export type TSConfigValues = Record<TTSType, TSTypeConfig & { enable: boolean }>;

export const defaultValues = Object.values(TSType).reduce((acc, type) => {
  acc[type] = { number: 1, enable: false };
  return acc;
}, {} as TSConfigValues);

export function toConfigDTO(data: TSConfigValues) {
  return Object.entries(data).reduce((acc, [key, { enable, ...config }]) => {
    acc[key as TTSType] = config;
    return acc;
  }, {} as TSConfigDTO);
}
