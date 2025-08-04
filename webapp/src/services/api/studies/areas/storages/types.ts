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

import type { IdentityDTO, StudyMetadata } from "@/types/types";
import type { PartialExceptFor } from "@/utils/tsUtils";
import type { O } from "ts-toolbelt";
import type { AdditionalConstraintOperator, AdditionalConstraintVariable } from "./constants";

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

export type AdditionalConstraintVariableValue = O.UnionOf<typeof AdditionalConstraintVariable>;

export type AdditionalConstraintOperatorValue = O.UnionOf<typeof AdditionalConstraintOperator>;

export type Hours = number[];

export interface AdditionalConstraint extends IdentityDTO {
  variable: AdditionalConstraintVariableValue;
  operator: AdditionalConstraintOperatorValue;
  occurrences: Array<{ hours: Hours }>;
  enabled: boolean;
}

export type AdditionalConstraintCreation = PartialExceptFor<
  Omit<AdditionalConstraint, "id">,
  "name"
>;

export type AdditionalConstraintUpdate = Partial<Omit<AdditionalConstraint, "id" | "name">>;

export interface GetAdditionalConstraintsParams {
  studyId: StudyMetadata["id"];
  areaId: string;
  storageId: string;
}

export interface GetAdditionalConstraintParams extends GetAdditionalConstraintsParams {
  constraintId: AdditionalConstraint["id"];
}

export interface CreateAdditionalConstraintsParams {
  studyId: StudyMetadata["id"];
  areaId: string;
  storageId: string;
  constraints: AdditionalConstraintCreation[];
}

export interface UpdateAdditionalConstraintsParams {
  studyId: StudyMetadata["id"];
  areaId: string;
  storageId: string;
  constraints: Record<AdditionalConstraint["id"], AdditionalConstraintUpdate>;
}

export interface DeleteAdditionalConstraintsParams {
  studyId: StudyMetadata["id"];
  areaId: string;
  constraintIds: Array<AdditionalConstraint["id"]>;
}
