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

import { createTableMode, deleteTableMode, updateTableMode } from "@/services/api/tablemode";
import { mutationOptions } from "@tanstack/react-query";
import { tableModeKeys } from "./keys";

export const tableModeMutations = {
  create: () => {
    return mutationOptions({
      mutationKey: tableModeKeys.create(),
      mutationFn: createTableMode,
    });
  },
  update: () => {
    return mutationOptions({
      mutationKey: tableModeKeys.update(),
      mutationFn: updateTableMode,
    });
  },
  delete: () => {
    return mutationOptions({
      mutationKey: tableModeKeys.delete(),
      mutationFn: deleteTableMode,
    });
  },
};
