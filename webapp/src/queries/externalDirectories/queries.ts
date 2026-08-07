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

import { getFavoriteExternalDirectories } from "@/services/api/favorites";
import { queryListOptions } from "../utils";
import { externalDirectoryKeys } from "./keys";

export const externalDirectoryQueries = {
  favorites: () => {
    return queryListOptions({
      queryKey: externalDirectoryKeys.favorites(),
      queryFn: getFavoriteExternalDirectories,
    });
  },
};
