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

import type { SvgIconComponent } from "@mui/icons-material";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import { compareAsc } from "date-fns";
import * as R from "ramda";
import { z } from "zod";
import type { StudyMetadata, StudySortConfig } from "@/types/types";

////////////////////////////////////////////////////////////////
// Schema
////////////////////////////////////////////////////////////////

export const SortPropertySchema = z.enum(["name", "modificationDate"]);
export const SortOrderSchema = z.enum(["ascend", "descend"]);

export const StudySortConfigSchema = z.object({
  property: SortPropertySchema,
  order: SortOrderSchema,
});

export const StudySortOptionSchema = z.object({
  id: z.string(),
  labelKey: z.string(),
  property: SortPropertySchema,
  order: SortOrderSchema,
  icon: z.custom<SvgIconComponent>((val) => typeof val === "function"),
});

export const StudySortOptionIdSchema = z.enum(["name-asc", "name-desc", "date-asc", "date-desc"]);

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type SortProperty = z.infer<typeof SortPropertySchema>;
export type SortOrder = z.infer<typeof SortOrderSchema>;
export type StudySortOption = z.infer<typeof StudySortOptionSchema>;
export type StudySortOptionId = z.infer<typeof StudySortOptionIdSchema>;

////////////////////////////////////////////////////////////////
// Options
////////////////////////////////////////////////////////////////

export const STUDY_SORT_OPTIONS = [
  {
    id: "name-asc",
    labelKey: "studies.sortByName",
    property: "name",
    order: "ascend",
    icon: ArrowUpwardIcon,
  },
  {
    id: "name-desc",
    labelKey: "studies.sortByName",
    property: "name",
    order: "descend",
    icon: ArrowDownwardIcon,
  },
  {
    id: "date-asc",
    labelKey: "studies.sortByDate",
    property: "modificationDate",
    order: "ascend",
    icon: ArrowUpwardIcon,
  },
  {
    id: "date-desc",
    labelKey: "studies.sortByDate",
    property: "modificationDate",
    order: "descend",
    icon: ArrowDownwardIcon,
  },
] as const satisfies readonly StudySortOption[];

////////////////////////////////////////////////////////////////
// Helpers
////////////////////////////////////////////////////////////////

const optionById = R.indexBy(R.prop("id"), STUDY_SORT_OPTIONS);
const optionByConfig = R.indexBy(
  (opt: StudySortOption) => `${opt.property}:${opt.order}`,
  STUDY_SORT_OPTIONS,
);

export const getStudySortOption = (id: StudySortOptionId): StudySortOption => optionById[id];

export const toStudySortConfig = R.pick(["property", "order"]) as (
  option: StudySortOption,
) => StudySortConfig;

export const findStudySortOptionId = (config: StudySortConfig): StudySortOptionId =>
  optionByConfig[`${config.property}:${config.order}`].id;

export const DEFAULT_STUDY_SORT_CONFIG: StudySortConfig = {
  property: "name",
  order: "ascend",
};

////////////////////////////////////////////////////////////////
// Sorting
////////////////////////////////////////////////////////////////

// Ascending comparators: return negative if a < b, positive if a > b
const compareByName = (a: StudyMetadata, b: StudyMetadata) => a.name.localeCompare(b.name);
const compareByDate = (a: StudyMetadata, b: StudyMetadata) =>
  compareAsc(a.modificationDate, b.modificationDate);

const ascendingComparators: Record<SortProperty, (a: StudyMetadata, b: StudyMetadata) => number> = {
  name: compareByName,
  modificationDate: compareByDate,
};

// Flip arguments to reverse sort order: compare(b, a) instead of compare(a, b)
const flipComparator =
  (compare: (a: StudyMetadata, b: StudyMetadata) => number) =>
  (a: StudyMetadata, b: StudyMetadata) =>
    compare(b, a);

export const sortStudies = R.curry(
  (config: StudySortConfig, studies: StudyMetadata[]): StudyMetadata[] => {
    const ascending = ascendingComparators[config.property];
    const comparator = config.order === "descend" ? flipComparator(ascending) : ascending;
    return R.sort(comparator, studies);
  },
);
