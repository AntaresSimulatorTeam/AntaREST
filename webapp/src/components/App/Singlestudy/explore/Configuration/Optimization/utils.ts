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

import type {
  ExportMpsOption,
  ExportMpsOption830,
  LegacyTransmissionCapacities,
  OptimizationFormFields,
  SimplexOptimizationRange,
  TransmissionCapacities,
  TransmissionCapacities840,
  UnfeasibleProblemBehavior,
} from "@/services/api/studies/config/optimization/types";
import { booleanToString, stringToBooleanOrIdentity } from "@/utils/booleanUtils";
import type { BooleanToStringOrIdentity } from "@/utils/tsUtils";
import * as R from "ramda";

export const UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS: UnfeasibleProblemBehavior[] = [
  "warning-dry",
  "warning-verbose",
  "error-dry",
  "error-verbose",
] as const;

export const SIMPLEX_OPTIMIZATION_RANGE_OPTIONS: SimplexOptimizationRange[] = [
  "day",
  "week",
] as const;

export const LEGACY_TRANSMISSION_CAPACITIES_OPTIONS: Array<
  BooleanToStringOrIdentity<LegacyTransmissionCapacities>
> = ["true", "false", "infinite"] as const;

export const TRANSMISSION_CAPACITIES_OPTIONS: TransmissionCapacities840[] = [
  "local-values",
  "null-for-all-links",
  "infinite-for-all-links",
  "null-for-physical-links",
  "infinite-for-physical-links",
] as const;

export const EXPORT_MPS_OPTIONS: ExportMpsOption830[] = [
  "none",
  "optim-1",
  "optim-2",
  "both-optims",
] as const;

export interface FormattedOptimizationFormFields
  extends Omit<OptimizationFormFields, "transmissionCapacities"> {
  transmissionCapacities: BooleanToStringOrIdentity<TransmissionCapacities>;
}

export const formatValuesForForm = (
  values: OptimizationFormFields,
  studyVersion: number,
): FormattedOptimizationFormFields =>
  R.evolve(
    {
      transmissionCapacities: (value: TransmissionCapacities) =>
        typeof value === "boolean" ? booleanToString(value) : value,
      exportMps: (value: ExportMpsOption) => {
        if (typeof value === "boolean" && studyVersion >= 830) {
          return value ? "both-optims" : "none";
        }
        return value;
      },
    },
    values,
  );

export const formatValuesForApi = (
  values: Partial<FormattedOptimizationFormFields>,
): Partial<OptimizationFormFields> =>
  R.evolve(
    {
      transmissionCapacities: (value: FormattedOptimizationFormFields["transmissionCapacities"]) =>
        stringToBooleanOrIdentity(value),
    },
    values,
  );
