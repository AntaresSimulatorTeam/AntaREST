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

import * as R from "ramda";
import type { StudyMetadata } from "../../../../../../types/types";
import client from "../../../../../../services/api/client";
import { WeekDay, type Month } from "@/utils/date";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

enum Mode {
  Economy = "Economy",
  Adequacy = "Adequacy",
  Expansion = "Expansion",
}

export enum BuildingMode {
  Automatic = "Automatic",
  Custom = "Custom",
  Derated = "Derated",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface GeneralFormFields {
  mode: Mode;
  firstDay: number;
  lastDay: number;
  horizon: string;
  firstMonth: Month;
  firstWeekDay: WeekDay;
  firstJanuary: WeekDay;
  leapYear: boolean;
  nbYears: number;
  buildingMode: BuildingMode;
  selectionMode: boolean;
  yearByYear: boolean;
  simulationSynthesis: boolean;
  mcScenario: boolean;
  // Geographic trimming + Thematic trimming.
  // For study versions < 710
  filtering?: boolean;
  // For study versions >= 710
  geographicTrimming?: boolean;
  thematicTrimming?: boolean;
}

export type SetDialogStateType = "thematicTrimming" | "scenarioPlaylist" | "scenarioBuilder" | "";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const MODE_OPTIONS: Array<{ label: string; value: Mode; tooltip?: string }> = [
  { label: "Economy", value: Mode.Economy },
  { label: "Adequacy", value: Mode.Adequacy },
  {
    label: "Economy (linear relaxation)",
    value: Mode.Expansion,
    tooltip: "study.configuration.general.mode.expansion.tooltip",
  },
];
export const BUILDING_MODE_OPTIONS = Object.values(BuildingMode);
export const FIRST_JANUARY_OPTIONS = Object.values(WeekDay);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/general/form`;
}

export async function getGeneralFormFields(
  studyId: StudyMetadata["id"],
): Promise<GeneralFormFields> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setGeneralFormFields(
  studyId: StudyMetadata["id"],
  values: Partial<GeneralFormFields>,
): Promise<void> {
  return client.put(makeRequestURL(studyId), values);
}

export const hasDayField = R.anyPass([R.has("firstDay"), R.has("lastDay"), R.has("leapYear")]);

export const pickDayFields = (
  values: GeneralFormFields,
): Pick<GeneralFormFields, "firstDay" | "lastDay" | "leapYear"> => {
  return R.pickAll(["firstDay", "lastDay", "leapYear"], values);
};
