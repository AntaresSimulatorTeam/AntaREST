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
import StatusDot from "@/components/icons/StatusDot";
import type { RouteListItem } from "@/components/page/list/RouterListView";
import type { QueryList } from "@/queries/types";
import { isQueryListItemOptimistic } from "@/queries/utils";
import type {
  BindingConstraint,
  BindingConstraintCreationDTO,
  BindingConstraintOperator,
  BindingConstraintOutputFilter,
  BindingConstraintTimeStep,
} from "@/services/api/studies/bindingConstraints/type";
import { sortByProp } from "@/services/utils";
import { linkOptions } from "@tanstack/react-router";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

const OPERATORS: readonly BindingConstraintOperator[] = ["less", "equal", "greater", "both"];
const TIME_STEPS: readonly BindingConstraintTimeStep[] = ["hourly", "daily", "weekly"];
const OUTPUT_FILTERS: readonly BindingConstraintOutputFilter[] = [
  "hourly",
  "daily",
  "weekly",
  "monthly",
  "annual",
];

export const OPERATOR_OPTIONS: Options<BindingConstraintOperator> = OPERATORS.map((operator) => ({
  label: (t) => t(`study.modeling.bindingConst.operator.${operator}`),
  value: operator,
}));

export const TIME_STEPS_OPTIONS: Options<BindingConstraintTimeStep> = TIME_STEPS.map(
  (timeStep) => ({
    label: (t) => t(`global.time.${timeStep}`),
    value: timeStep,
  }),
);

export const OUTPUT_FILTERS_OPTIONS: Options<BindingConstraintOutputFilter> = OUTPUT_FILTERS.map(
  (filter) => ({
    label: (t) => t(`global.time.${filter}`),
    value: filter,
  }),
);

export const DEFAULT_CONSTRAINT_VALUES = {
  name: "",
  enabled: true,
  timeStep: "hourly",
  operator: "equal",
  comments: "",
  terms: [],
  filterYearByYear: [],
  filterSynthesis: [],
  group: "default",
} satisfies BindingConstraintCreationDTO;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function bindingConstraintsToList(
  constraints: QueryList<BindingConstraint>,
): RouteListItem[] {
  const list = constraints.map((constraint) => ({
    id: constraint.id,
    label: constraint.name,
    icon: <StatusDot status={constraint.enabled ? "success" : "error"} size="xx-small" />,
    linkOptions: linkOptions({
      to: ".",
      params: { bindingConstraintId: constraint.id },
    }),
    loading: isQueryListItemOptimistic(constraint),
  }));

  return sortByProp("label", list);
}
