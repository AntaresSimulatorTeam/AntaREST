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
import type { PartialExceptFor } from "@/utils/tsUtils";
import type { O } from "ts-toolbelt";
import type {
  StorageAdditionalConstraintOperator,
  StorageAdditionalConstraintVariable,
} from "./constants";

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

export type StorageAdditionalConstraintVariableValue = O.UnionOf<
  typeof StorageAdditionalConstraintVariable
>;

export type StorageAdditionalConstraintOperatorValue = O.UnionOf<
  typeof StorageAdditionalConstraintOperator
>;

export interface StorageAdditionalConstraint {
  id: string;
  variable: StorageAdditionalConstraintVariableValue;
  operator: StorageAdditionalConstraintOperatorValue;
  hours: number[][];
  enabled: boolean;
}

export interface StorageAdditionalConstraintCreation
  extends Partial<Omit<StorageAdditionalConstraint, "id">> {
  name: string;
}

export interface GetStorageAdditionalConstraintsParams {
  studyId: StudyMetadata["id"];
  areaId: string;
  storageId: string;
}

export interface GetStorageAdditionalConstraintParams
  extends GetStorageAdditionalConstraintsParams {
  constraintId: StorageAdditionalConstraint["id"];
}

export interface CreateStorageAdditionalConstraintsParams {
  studyId: StudyMetadata["id"];
  areaId: string;
  storageId: string;
  constraints: StorageAdditionalConstraintCreation[];
}

export interface UpdateStorageAdditionalConstraintsParams {
  studyId: StudyMetadata["id"];
  areaId: string;
  storageId: string;
  constraints: Array<PartialExceptFor<StorageAdditionalConstraint, "id">>;
}

export interface DeleteStorageAdditionalConstraintsParams {
  studyId: StudyMetadata["id"];
  areaId: string;
  constraintIds: Array<StorageAdditionalConstraint["id"]>;
}
