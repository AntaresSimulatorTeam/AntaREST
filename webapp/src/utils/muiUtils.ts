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

import type { SxProps, Theme } from "@mui/material";

export function truncateTextSx(maxWidth?: number) {
  return {
    maxWidth,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  } satisfies SxProps<Theme>;
}

/**
 * Merges two `sx` props.
 *
 * This is useful when a custom component needs to accept an `sx` prop
 * and forward it to a MUI System component while applying its own base styles.
 *
 * @see {@link https://mui.com/system/getting-started/the-sx-prop/#passing-the-sx-prop}
 *
 * @param target - Base styles.
 * @param source - Styles that override the base styles.
 * @returns A merged `sx` prop with `source` overriding `target`.
 */
export function mergeSxProp(
  target: SxProps<Theme>,
  source: SxProps<Theme> | undefined,
): SxProps<Theme> {
  if (!source) {
    return target;
  }
  return [target, source].flatMap((sx) => (Array.isArray(sx) ? sx : [sx]));
}
