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

import { archiveOutput, deleteOutput, unarchiveOutput } from "@/services/api/studies/outputs";
import type { Study } from "@/services/api/studies/types";
import { mutationOptions } from "@tanstack/react-query";
import { outputKeys } from "./keys";

export const outputMutations = {
  delete: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: outputKeys.delete(studyId),
      mutationFn: deleteOutput,
    });
  },
  archive: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: outputKeys.archive(studyId),
      mutationFn: archiveOutput,
    });
  },
  unarchive: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: outputKeys.unarchive(studyId),
      mutationFn: unarchiveOutput,
    });
  },
};
