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

import type { SxProps, Theme } from "@mui/material";

export const fieldsPanelSx = {
  minHeight: 0,
  minWidth: 0,
  width: 1,
  flex: { md: 9 },
} satisfies SxProps<Theme>;

export const destinationPanelSx = {
  p: 1,
  pt: { xs: 3, md: 1 },
  pl: { xs: 1, md: 3 },
  borderTopWidth: { xs: 1, md: 0 },
  borderTopStyle: "solid",
  borderLeftWidth: { xs: 0, md: 1 },
  borderLeftStyle: "solid",
  borderColor: "divider",
  minWidth: 0,
  minHeight: 0,
  height: { xs: "clamp(320px, 50dvh, 480px)", md: 1 },
  // Give the directory explorer slightly more room than the form fields.
  flex: { md: 11 },
} satisfies SxProps<Theme>;
