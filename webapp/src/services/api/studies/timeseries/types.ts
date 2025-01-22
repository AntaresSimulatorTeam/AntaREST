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

import type { StudyMetadata } from "@/common/types.ts";
import type { DeepPartial } from "react-hook-form";
import type { F, O } from "ts-toolbelt";
import type { TSType } from "./constants";

export type TTSType = O.UnionOf<typeof TSType>;

export interface TSTypeConfig {
  number: number;
}

export type TSConfigDTO = Record<TTSType, TSTypeConfig>;

export interface SetTimeSeriesConfigParams<T> {
  studyId: StudyMetadata["id"];
  // Extra fields not allowed by the API
  values: DeepPartial<F.Exact<T, TSConfigDTO>>;
}
