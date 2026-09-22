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

import {
  createFavoriteExternalDirectory,
  deleteFavoriteExternalDirectory,
} from "@/services/api/favorites";
import { mutationOptions } from "@tanstack/react-query";
import { externalDirectoryKeys } from "./keys";

export const externalDirectoryMutations = {
  createFavorite: () => {
    return mutationOptions({
      mutationKey: externalDirectoryKeys.createFavorite(),
      mutationFn: createFavoriteExternalDirectory,
    });
  },
  deleteFavorite: () => {
    return mutationOptions({
      mutationKey: externalDirectoryKeys.deleteFavorite(),
      mutationFn: deleteFavoriteExternalDirectory,
    });
  },
};
