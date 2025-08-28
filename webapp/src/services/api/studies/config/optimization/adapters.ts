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

import { booleanToString, isBooleanString, stringToBoolean } from "@/utils/booleanUtils";
import type { OptimizationDTO, OptimizationForm } from "./types";

export function adaptOptimizationDtoToForm(
  dto: OptimizationDTO,
  studyVersion: number,
): OptimizationForm {
  const { transmissionCapacities, exportMps, ...rest } = dto;

  return {
    ...rest,
    transmissionCapacities:
      typeof transmissionCapacities === "boolean"
        ? booleanToString(transmissionCapacities)
        : transmissionCapacities,
    exportMps:
      typeof exportMps === "boolean" && studyVersion >= 830
        ? exportMps
          ? "both-optims"
          : "none"
        : exportMps,
  };
}

export function adaptOptimizationFormToDto(
  form: Partial<OptimizationForm>,
): Partial<OptimizationDTO> {
  const { transmissionCapacities, ...rest } = form;

  if (transmissionCapacities === undefined) {
    return rest;
  }

  return {
    ...rest,
    transmissionCapacities: isBooleanString(transmissionCapacities)
      ? stringToBoolean(transmissionCapacities)
      : transmissionCapacities,
  };
}
