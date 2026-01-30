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

/**
 * Gets the next item in the array after the item at the specified index is deleted.
 *
 * @param items - The array of items.
 * @param indexToDelete - The index of the item to be deleted.
 * @returns The next item after deletion, or `undefined` if not found.
 */
export function getNextItemAfterDeletion<T>(items: T[], indexToDelete: number) {
  if (indexToDelete < 0 || indexToDelete >= items.length) {
    return undefined;
  }
  return items[indexToDelete + 1] ?? items[indexToDelete - 1];
}
