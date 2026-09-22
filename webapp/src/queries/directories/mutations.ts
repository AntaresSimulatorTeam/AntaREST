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

import { createDirectory, deleteDirectory, updateDirectory } from "@/services/api/directories";
import { createFavoriteDirectory, deleteFavoriteDirectory } from "@/services/api/favorites";
import { mutationOptions } from "@tanstack/react-query";
import { directoryKeys } from "./keys";

export const directoryMutations = {
  create: () => {
    return mutationOptions({
      mutationKey: directoryKeys.create(),
      mutationFn: createDirectory,
    });
  },
  update: () => {
    return mutationOptions({
      mutationKey: directoryKeys.update(),
      mutationFn: updateDirectory,
    });
  },
  delete: () => {
    return mutationOptions({
      mutationKey: directoryKeys.delete(),
      mutationFn: deleteDirectory,
    });
  },
  createFavorite: () => {
    return mutationOptions({
      mutationKey: directoryKeys.createFavorite(),
      mutationFn: createFavoriteDirectory,
    });
  },
  deleteFavorite: () => {
    return mutationOptions({
      mutationKey: directoryKeys.deleteFavorite(),
      mutationFn: deleteFavoriteDirectory,
    });
  },
};
