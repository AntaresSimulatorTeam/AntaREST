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

import type { DeepPartial } from "react-hook-form";
import type { StudyMetadata } from "../../../../../../common/types";
import client from "../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export enum TSType {
  Load = "load",
  Hydro = "hydro",
  Thermal = "thermal",
  Wind = "wind",
  Solar = "solar",
  Renewables = "renewables",
  NTC = "ntc",
}

enum SeasonCorrelation {
  Monthly = "monthly",
  Annual = "annual",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

interface TSFormFieldsForType {
  stochasticTsStatus: boolean;
  number: number;
  refresh: boolean;
  refreshInterval: number;
  seasonCorrelation: SeasonCorrelation;
  storeInInput: boolean;
  storeInOutput: boolean;
  intraModal: boolean;
  interModal: boolean;
}

export interface TSFormFields
  extends Record<
    Exclude<TSType, TSType.Thermal | TSType.Renewables | TSType.NTC>,
    TSFormFieldsForType
  > {
  [TSType.Thermal]: Omit<TSFormFieldsForType, "seasonCorrelation">;
  [TSType.Renewables]: Pick<
    TSFormFieldsForType,
    "stochasticTsStatus" | "intraModal" | "interModal"
  >;
  [TSType.NTC]: Pick<TSFormFieldsForType, "stochasticTsStatus" | "intraModal">;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const DEFAULT_VALUES: DeepPartial<TSFormFields> = {
  thermal: {
    stochasticTsStatus: false,
    number: 1,
  },
};

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function setTimeSeriesFormFields(
  studyId: StudyMetadata["id"],
  values: DeepPartial<TSFormFields>,
): Promise<void> {
  return client.put(`v1/studies/${studyId}/config/timeseries/form`, values);
}
