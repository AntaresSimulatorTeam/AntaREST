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

import { getAssistantStatus } from "@/services/api/assistant";
import { queryOptions } from "@tanstack/react-query";
import { assistantKeys } from "./keys";

export const assistantQueries = {
  status: () => {
    return queryOptions({
      queryKey: assistantKeys.status(),
      queryFn: getAssistantStatus,
      // The status only changes with the configuration of the server
      staleTime: Infinity,
      // A server without assistant answers 404: the features of the assistant are then hidden
      retry: false,
    });
  },
};
