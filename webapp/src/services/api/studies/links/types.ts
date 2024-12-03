/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { O } from "ts-toolbelt";
import { AssetType, LinkStyle, TransmissionCapacity } from "./constants";
import { StudyMetadata } from "@/common/types";
import { PartialExceptFor } from "@/utils/tsUtils";

export type TTransmissionCapacity = O.UnionOf<typeof TransmissionCapacity>;

export type TAssetType = O.UnionOf<typeof AssetType>;

export type TLinkStyle = O.UnionOf<typeof LinkStyle>;

export interface LinkDTO {
  hurdlesCost: boolean;
  loopFlow: boolean;
  usePhaseShifter: boolean;
  transmissionCapacities: TTransmissionCapacity;
  assetType: TAssetType;
  displayComments: boolean;
  colorr: number;
  colorb: number;
  colorg: number;
  linkWidth: number;
  linkStyle: TLinkStyle;
  area1: string;
  area2: string;
  // Since v8.2
  filterSynthesis?: string;
  filterYearByYear?: string;
}

export interface CreateLinkParams
  extends PartialExceptFor<LinkDTO, "area1" | "area2"> {
  studyId: StudyMetadata["id"];
}

export interface DeleteLinkParams {
  studyId: StudyMetadata["id"];
  areaFrom: string;
  areaTo: string;
}
