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

import type { StorageCreation } from "@/services/api/studies/areas/storages/types";

export const DEFAULT_STORAGE_VALUES = {
  name: "",
  group: "",
  injectionNominalCapacity: 0,
  withdrawalNominalCapacity: 0,
  reservoirCapacity: 0,
  efficiency: 0,
  initialLevel: 0,
  initialLevelOptim: false,
} as const satisfies StorageCreation;
