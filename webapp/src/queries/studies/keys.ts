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

export const studyKeys = {
  all: () => ["studies"] as const,
  deleteMany: () => [...studyKeys.all(), "deleteStudies"] as const,
  favorites: () => [...studyKeys.all(), "favoriteStudies"] as const,
  createFavorite: () => [...studyKeys.favorites(), "createFavoriteStudy"] as const,
  deleteFavorite: () => [...studyKeys.favorites(), "deleteFavoriteStudy"] as const,
  // Variants
  allVariants: () => [...studyKeys.all(), "variants"] as const,
  variantTree: (studyId: string) =>
    [...studyKeys.allVariants(), "variantTree", { studyId }] as const,
};
