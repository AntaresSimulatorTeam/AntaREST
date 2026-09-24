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

import type { Storage } from "@/services/api/studies/areas/storages/types";

/**
 * Keeps legacy table/form defaults out of the API cache.
 *
 * @param storage - Validated storage from the API.
 * @returns Storage with defaults for table and form fields.
 */
export function adaptStorageToView(storage: Storage) {
  return {
    ...storage,
    group: storage.group ?? "",
    enabled: storage.enabled ?? false,
    efficiencyWithdrawal: storage.efficiencyWithdrawal ?? -1,
    penalizeVariationInjection: storage.penalizeVariationInjection ?? false,
    penalizeVariationWithdrawal: storage.penalizeVariationWithdrawal ?? false,
    allowOverflow: storage.allowOverflow ?? false,
  };
}
