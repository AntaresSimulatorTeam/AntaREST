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

import type { PartialExceptFor } from "@/utils/tsUtils";

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

export type ConstraintVariable = "withdrawal" | "injection" | "netting";

export type ConstraintOperator = "less" | "greater" | "equal";

export interface AdditionalConstraint {
  id: string;
  name: string;
  variable: ConstraintVariable;
  operator: ConstraintOperator;
  occurrences: Array<{ hours: number[] }>;
  enabled: boolean;
}

export type AdditionalConstraintCreation = PartialExceptFor<
  Omit<AdditionalConstraint, "id">,
  "name"
>;

export type AdditionalConstraintUpdate = Partial<AdditionalConstraint> & {
  id?: never;
  name?: never;
};

export interface BaseStorageParams {
  studyId: string;
  areaId: string;
  storageId: string;
}

export type GetAdditionalConstraintsParams = BaseStorageParams;

export interface GetAdditionalConstraintParams extends BaseStorageParams {
  constraintId: AdditionalConstraint["id"];
}

export interface CreateAdditionalConstraintsParams extends BaseStorageParams {
  constraints: AdditionalConstraintCreation[];
}

export interface UpdateAdditionalConstraintsParams extends BaseStorageParams {
  constraints: Record<AdditionalConstraint["id"], AdditionalConstraintUpdate>;
}

export interface DeleteAdditionalConstraintsParams extends BaseStorageParams {
  constraintIds: Array<AdditionalConstraint["id"]>;
}
