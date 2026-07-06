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

import type { Options } from "@/components/fieldEditors/SelectFE";
import {
  isAreaOrDistrict,
  isLink,
  type DataType,
  type Frequency,
  type Item,
  type MonteCarloMode,
} from "../../../../-utils";

export const MONTE_CARLO_MODE_OPTIONS = [
  { value: "mc-all", label: "Synthesis" },
  { value: "mc-ind", label: "Year by year" },
  { value: "variable-per-variable", label: (t) => t("study.outputs.variablePerVariable") },
] as const satisfies Options<MonteCarloMode>;

const DATATYPE_OPTIONS = [
  { value: "values", label: "General values" },
  { value: "details", label: "Thermal plants" },
  { value: "details-res", label: "Ren. clusters" },
  { value: "id", label: "RecordYears" },
  { value: "details-STstorage", label: "ST Storages" },
] as const satisfies Options<DataType>;

export const FREQUENCY_OPTIONS = [
  { value: "hourly", label: (t) => t("global.time.hourly") },
  { value: "daily", label: (t) => t("global.time.daily") },
  { value: "weekly", label: (t) => t("global.time.weekly") },
  { value: "monthly", label: (t) => t("global.time.monthly") },
  { value: "annual", label: (t) => t("global.time.annual") },
] as const satisfies Options<Frequency>;

export function getDataTypeOptions(item: Item, monteCarloMode: MonteCarloMode) {
  if (monteCarloMode === "variable-per-variable") {
    if (isAreaOrDistrict(item)) {
      return DATATYPE_OPTIONS.filter((option) => option.value !== "id");
    }

    if (isLink(item)) {
      return DATATYPE_OPTIONS.filter((option) => option.value === "values");
    }
  }

  return DATATYPE_OPTIONS;
}
