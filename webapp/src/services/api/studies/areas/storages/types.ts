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
import { F } from "ts-toolbelt";

export interface BaseStorageParams {
  studyId: string;
  areaId: string;
  storageId: string;
}

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

export type AdditionalConstraintVariable = "withdrawal" | "injection" | "netting";

export type AdditionalConstraintOperator = "less" | "greater" | "equal";

export interface AdditionalConstraint {
  id: string;
  name: string;
  variable: AdditionalConstraintVariable;
  operator: AdditionalConstraintOperator;
  occurrences: Array<{ hours: number[] }>;
  enabled: boolean;
}

export type AdditionalConstraintCreation = PartialExceptFor<
  Omit<AdditionalConstraint, "id">,
  "name"
>;

export type AdditionalConstraintUpdate = Partial<Omit<AdditionalConstraint, "id" | "name">>;

export interface GetAdditionalConstraintParams extends BaseStorageParams {
  constraintId: AdditionalConstraint["id"];
}

export interface CreateAdditionalConstraintsParams<T> extends BaseStorageParams {
  constraints: Array<F.Exact<T, AdditionalConstraintCreation>>;
}

export interface UpdateAdditionalConstraintsParams<T> extends BaseStorageParams {
  constraints: Record<AdditionalConstraint["id"], F.Exact<T, AdditionalConstraintUpdate>>;
}

export interface DeleteAdditionalConstraintsParams extends BaseStorageParams {
  constraintIds: Array<AdditionalConstraint["id"]>;
}
