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

import { Box, Drawer, styled } from "@mui/material";

export const Root = styled(Drawer)({
  width: "50%",
  flexShrink: 0,
  "& .MuiDrawer-paper": {
    width: "50%",
    boxSizing: "border-box",
    overflow: "hidden",
  },
});

export const TitleContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  width: "100%",
  height: "100%",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  padding: theme.spacing(1, 0),
  flexDirection: "column",
  flexWrap: "nowrap",
  boxSizing: "border-box",
  color: "white",
}));
