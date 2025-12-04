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

import { isValidElement } from "react";

/**
 * Validates that sizes array is valid for react-split.
 * Sizes must be numbers that sum to 100 (percentage).
 *
 * @param sizes - Array of numbers representing the sizes of the split view
 * @returns true if sizes is a valid array of numbers that sum to 100
 */
export function isValidSizes(sizes: unknown): sizes is number[] {
  if (!Array.isArray(sizes) || sizes.length === 0) {
    return false;
  }

  return (
    sizes.every((size) => typeof size === "number") &&
    sizes.reduce((sum, size) => sum + size, 0) === 100
  );
}

/**
 * Extracts a type identifier from a React element's type.
 *
 * @param type - The type property of a React element (string, function, or object)
 * @returns The type identifier string, or undefined if it cannot be determined
 */
function getTypeId(type: React.ReactElement["type"]): string | undefined {
  if (typeof type === "string") {
    return type;
  }

  if (typeof type === "function") {
    return type.name || undefined;
  }

  if (type && typeof type === "object") {
    const { name, displayName } = type as { name?: string; displayName?: string };
    return name || displayName;
  }

  return undefined;
}

/**
 * Generates a stable key for a React child element.
 * This prevents DOM ref issues with react-split when children change conditionally.
 *
 * The key is based on:
 * 1. The child's existing key (if provided)
 * 2. The component type (function/class name or element type)
 * 3. The child's position index
 *
 * This ensures that when conditional rendering swaps children (e.g., SynthesisViewer <-> ResultMatrixViewer),
 * react-split's internal DOM refs are properly updated instead of being reused incorrectly.
 *
 * @param child - React child element
 * @param index - Position index of the child
 * @returns Stable key string
 */
export function getChildKey(child: React.ReactNode, index: number): string {
  if (!isValidElement(child)) {
    return `split-child-${index}`;
  }

  if (child.key !== null && child.key !== undefined) {
    return String(child.key);
  }

  const typeId = getTypeId(child.type) ?? "unknown";

  return `split-${typeId}-${index}`;
}
