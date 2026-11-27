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

import { QueryClient } from "@tanstack/react-query";
import { minutesToMilliseconds } from "date-fns";

/** Cached query data stays fresh for one minute by default. */
export const DEFAULT_STALE_TIME_MS = minutesToMilliseconds(1);

/**
 * Note: use `useQueryClient()` instead of importing this directly in React components.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: DEFAULT_STALE_TIME_MS,
    },
  },
});
