/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import type { RoleType, UserDTO } from "@/types/types";

interface GroupPermission {
  user: UserDTO;
  type: RoleType;
}

export interface GroupFormDefaultValues {
  name: string;
  permissions: GroupPermission[];
}

export const GROUP_FORM_DEFAULT_VALUES: GroupFormDefaultValues = {
  name: "",
  permissions: [],
} as const;
