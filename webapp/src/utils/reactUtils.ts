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

import { setRef } from "@mui/material";

export function isDependencyList(
  value: unknown,
): value is React.DependencyList {
  return Array.isArray(value);
}

export function composeRefs(
  ...refs: Array<React.Ref<unknown> | undefined | null>
) {
  return function refCallback(instance: unknown): void {
    refs.forEach((ref) => setRef(ref, instance));
  };
}

export function getComponentDisplayName<T>(
  comp: React.ComponentType<T>,
): string {
  return comp.displayName || comp.name || "Component";
}
