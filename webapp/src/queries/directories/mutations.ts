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

import { mutationOptions } from "@tanstack/react-query";
import { directoriesApi } from "@/services/api/directories";
import type { CreateDirectoryInput, UpdateDirectoryInput } from "@/services/api/directories/types";

export const directoryMutations = {
  create: () => {
    return mutationOptions({
      mutationKey: ["createDirectory"],
      mutationFn: (directoryData: CreateDirectoryInput) => directoriesApi.create(directoryData),
    });
  },

  update: () => {
    return mutationOptions({
      mutationKey: ["updateDirectory"],
      mutationFn: ({ id, data }: { id: string; data: UpdateDirectoryInput }) =>
        directoriesApi.update(id, data),
    });
  },

  delete: () => {
    return mutationOptions({
      mutationKey: ["deleteDirectory"],
      mutationFn: (directoryId: string) => directoriesApi.delete(directoryId),
    });
  },
};
