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

import type { StorageConstraintOccurrences } from "@/services/api/studies/areas/storages/types";
import type { DeepPartial } from "react-hook-form";

/**
 * Checks if the occurrences array contains at least one occurrence with non-empty hours.
 *
 * @param occurrences - The value to check.
 * @returns `true` if at least one occurrence has non-empty hours, `false` otherwise.
 */
export const isOccurrencesValid = (
  occurrences: DeepPartial<StorageConstraintOccurrences> | undefined,
) => {
  return !!occurrences?.find((occ) => occ?.hours && occ.hours.length > 0);
};
