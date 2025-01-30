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

import type { GenericInfo } from "../../../common/types";

export const PUBLIC_MODE_LIST: GenericInfo[] = [
  { id: "NONE", name: "study.nonePublicMode" },
  { id: "READ", name: "study.readPublicMode" },
  { id: "EXECUTE", name: "study.executePublicMode" },
  { id: "EDIT", name: "global.edit" },
  { id: "FULL", name: "study.fullPublicMode" },
];

export const ROOT_FOLDER_NAME = "root";
export const DEFAULT_WORKSPACE_PREFIX = `${ROOT_FOLDER_NAME}/default`;
