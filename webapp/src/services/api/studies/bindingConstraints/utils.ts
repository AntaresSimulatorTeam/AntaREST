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

import type {
  BindingConstraintClusterTerm,
  BindingConstraintLinkTerm,
  BindingConstraintTerm,
} from "./type";

export type BindingConstraintTermType = "link" | "cluster";

export function isBindingConstraintLinkTerm(
  term: BindingConstraintTerm,
): term is BindingConstraintLinkTerm {
  return "area1" in term.data && "area2" in term.data;
}

export function isBindingConstraintClusterTerm(
  term: BindingConstraintTerm,
): term is BindingConstraintClusterTerm {
  return "area" in term.data && "cluster" in term.data;
}

export function getBindingConstraintTermType(
  term: BindingConstraintTerm,
): BindingConstraintTermType | undefined {
  if (isBindingConstraintLinkTerm(term)) {
    return "link";
  }
  if (isBindingConstraintClusterTerm(term)) {
    return "cluster";
  }
  return;
}
