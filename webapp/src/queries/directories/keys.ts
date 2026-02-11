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

export const directoryKeys = {
  all: ["directories"] as const,
  lists: () => [...directoryKeys.all, "list"] as const,
  details: () => [...directoryKeys.all, "detail"] as const,
  detail: (id: string) => [...directoryKeys.details(), id] as const,
  create: () => [...directoryKeys.all, "createDirectory"] as const,
  update: () => [...directoryKeys.all, "updateDirectory"] as const,
  delete: () => [...directoryKeys.all, "deleteDirectory"] as const,
};
