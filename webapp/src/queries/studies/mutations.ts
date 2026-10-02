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

import { createFavoriteStudy, deleteFavoriteStudy } from "@/services/api/favorites";
import { deleteStudies } from "@/services/api/study";
import { mutationOptions } from "@tanstack/react-query";
import { studyKeys } from "./keys";

export const studyMutations = {
  deleteMany: () => {
    return mutationOptions({
      mutationKey: studyKeys.deleteMany(),
      mutationFn: deleteStudies,
    });
  },
  createFavorite: () => {
    return mutationOptions({
      mutationKey: studyKeys.createFavorite(),
      mutationFn: createFavoriteStudy,
    });
  },
  deleteFavorite: () => {
    return mutationOptions({
      mutationKey: studyKeys.deleteFavorite(),
      mutationFn: deleteFavoriteStudy,
    });
  },
};
