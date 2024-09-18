/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { SxProps, Theme } from "@mui/material";

export function mergeSxProp(
  target: SxProps<Theme> = {},
  source: SxProps<Theme> = [],
): SxProps<Theme> {
  // https://mui.com/system/getting-started/the-sx-prop/#passing-the-sx-prop
  return [target, ...(Array.isArray(source) ? source : [source])];
}
