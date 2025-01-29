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

import { styled } from "@mui/material";

export const Menubar = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  gap: theme.spacing(1),
}));

export const Filename = styled((props: { children?: string }) => (
  <div title={props.children} {...props} />
))(({ theme }) => ({
  flex: 1,
  overflow: "hidden",
  textOverflow: "ellipsis",
  color: theme.palette.text.secondary,
}));
