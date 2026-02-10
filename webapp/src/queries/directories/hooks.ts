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

import { useSuspenseQuery } from "@tanstack/react-query";
import { directoryQueries } from "./queries";

export const useDirectory = (directoryId: string) => {
  return useSuspenseQuery({
    ...directoryQueries.list(),
    select: (directories) => {
      const directory = directories.find((dir) => dir.id === directoryId);

      if (!directory) {
        throw new Error(`Directory with id ${directoryId} not found`);
      }

      return directory;
    },
  });
};
