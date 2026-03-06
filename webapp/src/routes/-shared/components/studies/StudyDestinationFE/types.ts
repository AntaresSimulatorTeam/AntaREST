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
 * One clickable segment in the address bar breadcrumb.
 * `id === null` represents the virtual root.
 */
export interface BreadcrumbSegment {
  id: string | null;
  name: string;
  /** Whether this segment is the currently navigated directory. */
  active?: boolean;
}

export interface DirectoryDestination {
  /** ID of the currently active directory in the explorer, or `null` for the managed root. */
  directoryId: string | null;
  /**
   * Slash-separated path of new sub-directories to create beneath the active
   * directory (e.g. `"a"` or `"a/b/c"`).
   * Empty string when an existing directory was selected as-is.
   */
  newSubdirectoriesPath: string;
}
