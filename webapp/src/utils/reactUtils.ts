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

import { setRef } from "@mui/material";

export function isDependencyList(value: unknown): value is React.DependencyList {
  return Array.isArray(value);
}

export function composeRefs(...refs: Array<React.Ref<unknown> | undefined | null>) {
  return function refCallback(instance: unknown): void {
    refs.forEach((ref) => {
      setRef(ref, instance);
    });
  };
}

export function getComponentDisplayName<T>(comp: React.ComponentType<T>): string {
  return comp.displayName || comp.name || "Component";
}

type Primitive = string | number | boolean;

function encode(value: Primitive): string {
  if (typeof value === "number") {
    if (Object.is(value, -0)) {
      return "-0";
    }
    if (!Number.isFinite(value)) {
      return String(value);
    }
  }
  return JSON.stringify(value);
}

/**
 * Builds a deterministic string key from primitives, arrays of primitives
 * and flat objects of primitives. Meant to be used as a React `key`.
 *
 * Each value is written on its own line, and the lines are joined with `\n`:
 * - `"a"` → `"a"`
 * - `1` → `1`
 * - `["a", 1]` → `[2]`, `"a"`, `1`
 * - `{ b: 2, a: 1 }` → `{2}`, `"a"=1`, `"b"=2`
 *
 * Two different inputs never produce the same key:
 * - Strings are quoted, so `1` !== `"1"` and `true` !== `"true"`.
 * - Line breaks in values and object keys are escaped, so they can't fake an extra line.
 * - Arrays and objects start with a size header (`[n]` / `{n}`), so `[]`, `{}`,
 *   `["a", "b"]` and `"a", "b"` all differ.
 *
 * Array order is preserved, while object keys are sorted
 * (`{ a: 1, b: 2 }` === `{ b: 2, a: 1 }`).
 *
 * @param items - Primitives, arrays of primitives or flat objects of primitives.
 * @returns A multi-line string that uniquely identifies the given items.
 */
export function buildKey(...items: Array<Primitive[] | Primitive | Record<string, Primitive>>) {
  const lines: string[] = [];

  for (const item of items) {
    if (Array.isArray(item)) {
      lines.push(`[${item.length}]`);
      for (const value of item) {
        lines.push(encode(value));
      }
      continue;
    }

    if (typeof item === "object") {
      const keys = Object.keys(item).sort();
      lines.push(`{${keys.length}}`);
      for (const key of keys) {
        lines.push(`${JSON.stringify(key)}=${encode(item[key])}`);
      }
      continue;
    }

    lines.push(encode(item));
  }

  return lines.join("\n");
}
