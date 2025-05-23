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
import type { AssetType, LinkStyle, TransmissionCapacity } from "./constants";

export type TransmissionCapacityValue = O.UnionOf<typeof TransmissionCapacity>;

export type AssetTypeValue = O.UnionOf<typeof AssetType>;

export type LinkStyleValue = O.UnionOf<typeof LinkStyle>;

export type FilterLink = Array<"hourly" | "daily" | "weekly" | "monthly" | "annual">;

export interface LinkDTO {
  hurdlesCost: boolean;
  loopFlow: boolean;
  usePhaseShifter: boolean;
  transmissionCapacities: TransmissionCapacityValue;
  assetType: AssetTypeValue;
  displayComments: boolean;
  colorr: number;
  colorb: number;
  colorg: number;
  linkWidth: number;
  linkStyle: LinkStyleValue;
  area1: string;
  area2: string;
  // Since v8.2
  filterSynthesis?: string;
  filterYearByYear?: string;
}

export interface Link extends Omit<LinkDTO, "filterSynthesis" | "filterYearByYear"> {
  id: string;
  // Since v8.2
  filterSynthesis?: FilterLink;
  filterYearByYear?: FilterLink;
}

export interface GetLinksParams {
  studyId: StudyMetadata["id"];
}

export interface GetLinkParams {
  studyId: StudyMetadata["id"];
  linkId: Link["id"];
}

export interface UpdateLinkParams {
  studyId: StudyMetadata["id"];
  linkId: Link["id"];
  config: Partial<Omit<Link, "id" | "area1" | "area2">>;
}

export interface CreateLinkParams extends PartialExceptFor<LinkDTO, "area1" | "area2"> {
  studyId: StudyMetadata["id"];
}

export interface DeleteLinkParams {
  studyId: StudyMetadata["id"];
  linkId: Link["id"];
}
