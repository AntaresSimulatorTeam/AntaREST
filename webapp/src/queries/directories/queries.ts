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

import { getDirectories } from "@/services/api/directories";
import { getFavoriteDirectories } from "@/services/api/favorites";
import { queryOptions } from "@tanstack/react-query";
import { queryListOptions } from "../utils";
import { directoryKeys } from "./keys";

export const directoryQueries = {
  list: () => {
    return queryOptions({
      queryKey: directoryKeys.list(),
      queryFn: getDirectories,
    });
  },
  favorites: () => {
    return queryListOptions({
      queryKey: directoryKeys.favorites(),
      queryFn: getFavoriteDirectories,
    });
  },
};
