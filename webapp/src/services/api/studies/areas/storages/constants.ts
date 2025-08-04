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

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

export const AdditionalConstraintVariable = {
  Withdrawal: "withdrawal",
  Injection: "injection",
  Netting: "netting",
} as const;

export const AdditionalConstraintOperator = {
  Less: "less",
  Greater: "greater",
  Equal: "equal",
} as const;
