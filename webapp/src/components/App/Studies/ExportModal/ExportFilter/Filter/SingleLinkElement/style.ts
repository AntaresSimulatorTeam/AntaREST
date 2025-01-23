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

import { Box, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "center",
  alignItem: "center",
  boxSizing: "border-box",
}));

export const LinkFilter = styled(Box)(({ theme }) => ({
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  boxSizing: "border-box",
  padding: 0,
  flexGrow: 1,
  overflow: "hidden",
}));

export default {};
