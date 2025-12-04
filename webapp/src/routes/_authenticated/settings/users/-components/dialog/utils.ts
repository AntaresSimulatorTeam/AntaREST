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

import type { GroupDTO, RoleType } from "@/types/types";

interface UserPermission {
  group: GroupDTO;
  type: RoleType;
}

export interface UserFormDefaultValues {
  username: string;
  password: string;
  confirmPassword: string;
  permissions: UserPermission[];
}

export const USER_FORM_DEFAULT_VALUES: UserFormDefaultValues = {
  username: "",
  password: "",
  confirmPassword: "",
  permissions: [],
} as const;
