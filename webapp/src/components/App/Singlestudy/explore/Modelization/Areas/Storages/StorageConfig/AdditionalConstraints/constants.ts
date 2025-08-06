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

export const CONSTRAINT_VARIABLES = [
  { value: "withdrawal", label: "study.modelization.storages.additionalConstraints.charge" },
  { value: "injection", label: "study.modelization.storages.additionalConstraints.discharge" },
  { value: "netting", label: "study.modelization.storages.additionalConstraints.level" },
] as const;

export const CONSTRAINT_OPERATORS = [
  { value: "less", label: "<" },
  { value: "equal", label: "=" },
  { value: "greater", label: ">" },
] as const;

import type { AdditionalConstraintCreation } from "@/services/api/studies/areas/storages/types";

export const DEFAULT_CONSTRAINT_VALUES: AdditionalConstraintCreation = {
  name: "",
  variable: "withdrawal",
  operator: "less",
  enabled: true,
  occurrences: [],
};
