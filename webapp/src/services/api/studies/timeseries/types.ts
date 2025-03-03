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

import type { StudyMetadata } from "@/types/types";
import type { DeepPartial } from "react-hook-form";
import type { O } from "ts-toolbelt";
import { type TimeSeriesType } from "./constants";

export type TimeSeriesTypeValue = O.UnionOf<typeof TimeSeriesType>;

export interface TimeSeriesTypeConfig {
  number: number;
}

export type TimeSeriesConfigDTO = Record<TimeSeriesTypeValue, TimeSeriesTypeConfig>;

export interface SetTimeSeriesConfigParams {
  studyId: StudyMetadata["id"];
  values: DeepPartial<TimeSeriesConfigDTO>;
}
