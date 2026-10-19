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

import type { AreaWithId, StudyMetadata } from "@/types/types";
import type { PartialExceptFor } from "@/utils/tsUtils";
import type { z } from "zod";
import type {
  storageCreationSchema,
  storageGroupSchema,
  storageSchema,
  storageUpdateSchema,
} from "./schemas";

export type StorageGroup = z.infer<typeof storageGroupSchema>;
export type Storage = z.infer<typeof storageSchema>;
export type StorageResponse = z.input<typeof storageSchema>;
export type StorageCreation = z.input<typeof storageCreationSchema>;
export type StorageUpdate = z.input<typeof storageUpdateSchema>;

export interface StoragesAreaParams {
  studyId: StudyMetadata["id"];
  areaId: AreaWithId["id"];
}

export interface StorageParams extends StoragesAreaParams {
  storageId: Storage["id"];
}

export interface CreateStorageParams extends StoragesAreaParams {
  values: StorageCreation;
}

export interface UpdateStorageParams extends StorageParams {
  values: StorageUpdate;
}

export interface DuplicateStorageParams extends StorageParams {
  newName: Storage["name"];
}

export interface DeleteStoragesParams extends StoragesAreaParams {
  storageIds: Array<Storage["id"]>;
}

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

export type StorageConstraintVariable = "withdrawal" | "injection" | "netting";

export type StorageConstraintOperator = "less" | "greater" | "equal";

export type StorageConstraintOccurrences = Array<{ hours: number[] }>;

export interface StorageConstraint {
  id: string;
  name: string;
  variable: StorageConstraintVariable;
  operator: StorageConstraintOperator;
  occurrences: StorageConstraintOccurrences;
  enabled: boolean;
}

export type StorageConstraintCreation = PartialExceptFor<Omit<StorageConstraint, "id">, "name">;

export type StorageConstraintUpdate = Partial<Omit<StorageConstraint, "id" | "name">>;

export interface GetStorageConstraintParams extends StorageParams {
  constraintId: StorageConstraint["id"];
}

export interface CreateStorageConstraintsParams extends StorageParams {
  constraints: StorageConstraintCreation[];
}

export interface CreateStorageConstraintParams extends StorageParams {
  values: StorageConstraintCreation;
}

export interface UpdateStorageConstraintsParams extends StorageParams {
  constraints: Record<StorageConstraint["id"], StorageConstraintUpdate>;
}

export interface UpdateStorageConstraintParams extends StorageParams {
  constraintId: StorageConstraint["id"];
  values: StorageConstraintUpdate;
}

export interface DeleteStorageConstraintsParams extends StorageParams {
  constraintIds: Array<StorageConstraint["id"]>;
}

export interface DeleteStorageConstraintParams extends StorageParams {
  constraintId: StorageConstraint["id"];
}
