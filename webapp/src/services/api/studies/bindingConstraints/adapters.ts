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

import * as R from "ramda";
import semver from "semver";
import type {
  BindingConstraint,
  BindingConstraintCreationDTO,
  BindingConstraintDTO,
  BindingConstraintOutputFilter,
  BindingConstraintUpdateDTO,
} from "./type";

export function adaptBindingConstraintOutputFilterStringToArray(
  value: BindingConstraintDTO["filterYearByYear"] | BindingConstraintDTO["filterSynthesis"],
): BindingConstraintOutputFilter[] {
  if (!value?.trim()) {
    return [];
  }

  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean) as BindingConstraintOutputFilter[];
}

export function adaptBindingConstraintDtoToBindingConstraint(
  dto: BindingConstraintDTO,
): BindingConstraint {
  const transformations = {
    filterYearByYear: adaptBindingConstraintOutputFilterStringToArray,
    filterSynthesis: adaptBindingConstraintOutputFilterStringToArray,
  };

  return R.evolve(transformations, dto);
}

export function adaptBindingConstraintOperationDtoToStudyVersion<
  T extends BindingConstraintCreationDTO | BindingConstraintUpdateDTO,
>(dto: T, studyVersion: string): T {
  let adaptedDto = { ...dto };

  if (semver.lt(studyVersion, "8.7.0")) {
    adaptedDto = R.omit(["group"], adaptedDto) as T;
  }

  if (semver.lt(studyVersion, "8.3.0")) {
    adaptedDto = R.omit(["filterYearByYear", "filterSynthesis"], adaptedDto) as T;
  }

  return adaptedDto;
}
