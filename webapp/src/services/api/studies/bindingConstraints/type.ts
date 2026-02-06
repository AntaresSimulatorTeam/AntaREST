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

import type { StudyMetadata } from "@/types/types";
import type { PartialExceptFor } from "@/utils/tsUtils";

export type BindingConstraintTimeStep = "hourly" | "daily" | "weekly";

export type BindingConstraintOperator = "less" | "greater" | "both" | "equal";

export type BindingConstraintOutputFilter = "hourly" | "daily" | "weekly" | "monthly" | "annual";

export interface BindingConstraintLinkTermData {
  area1: string;
  area2: string;
}

export interface BindingConstraintClusterTermData {
  area: string;
  cluster: string;
}

export type BindingConstraintTermData =
  | BindingConstraintLinkTermData
  | BindingConstraintClusterTermData;

export interface BindingConstraintTerm<
  T extends BindingConstraintTermData = BindingConstraintTermData,
> {
  weight: number;
  offset?: number;
  data: T;
}

export type BindingConstraintLinkTerm = BindingConstraintTerm<BindingConstraintLinkTermData>;

export type BindingConstraintClusterTerm = BindingConstraintTerm<BindingConstraintClusterTermData>;

export interface BindingConstraintDTO {
  id: string;
  name: string;
  enabled: boolean;
  timeStep: BindingConstraintTimeStep;
  operator: BindingConstraintOperator;
  comments: string;
  terms: BindingConstraintTerm[];
  // Since v8.3
  filterYearByYear?: string | null; // For versions < v8.3, this field may be null instead of undefined
  filterSynthesis?: string | null; // For versions < v8.3, this field may be null instead of undefined
  // Since v8.7
  group?: string;
}

export interface BindingConstraint
  extends Omit<BindingConstraintDTO, "filterYearByYear" | "filterSynthesis"> {
  // Since v8.3
  filterYearByYear?: BindingConstraintOutputFilter[];
  filterSynthesis?: BindingConstraintOutputFilter[];
}

interface BindingConstraintMatrices {
  // 2nd member matrix for studies before v8.7
  values?: number[][] | string;
  // Less term matrix for v8.7+ studies
  lessTermMatrix?: number[][] | string;
  // Greater term matrix for v8.7+ studies
  greaterTermMatrix?: number[][] | string;
  // Equal term matrix for v8.7+ studies
  equalTermMatrix?: number[][] | string;
}

export interface BindingConstraintCreationDTO
  extends PartialExceptFor<
      Omit<BindingConstraintDTO, "id" | "filterYearByYear" | "filterSynthesis">,
      "name"
    >,
    BindingConstraintMatrices {
  // Since v8.3
  filterYearByYear?: BindingConstraintOutputFilter[]; // String type not included for convenience
  filterSynthesis?: BindingConstraintOutputFilter[]; // String type not included for convenience
}

export type BindingConstraintUpdateDTO = Omit<BindingConstraintCreationDTO, "name">;

export interface GetBindingConstraintParams {
  studyId: StudyMetadata["id"];
  constraintId: BindingConstraintDTO["id"];
}

export interface GetBindingConstraintsParams {
  studyId: StudyMetadata["id"];
  filters?: {
    enabled?: boolean;
    operator?: BindingConstraintOperator;
    comments?: string;
    group?: string;
    timeStep?: BindingConstraintTimeStep;
    areaName?: string;
    clusterName?: string;
    linkId?: string;
    clusterId?: string;
  };
}

export interface CreateBindingConstraintsParams {
  studyId: StudyMetadata["id"];
  studyVersion: StudyMetadata["version"];
  values: BindingConstraintCreationDTO;
}

export interface UpdateBindingConstraintsParams {
  studyId: StudyMetadata["id"];
  studyVersion: StudyMetadata["version"];
  constraintId: BindingConstraintDTO["id"];
  values: BindingConstraintUpdateDTO;
}

export interface DuplicateBindingConstraintParams {
  studyId: StudyMetadata["id"];
  constraintId: BindingConstraintDTO["id"];
  newConstraintName: BindingConstraintDTO["name"];
}

export interface DeleteBindingConstraintParams {
  studyId: StudyMetadata["id"];
  constraintId: BindingConstraintDTO["id"];
}
