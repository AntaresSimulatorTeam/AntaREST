/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Box, styled, Typography } from "@mui/material";

export const MatrixContainer = styled(Box)(() => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  overflow: "hidden",
}));

export const MatrixHeader = styled(Box)(() => ({
  width: "100%",
  display: "flex",
  flexFlow: "row wrap",
  justifyContent: "space-between",
  alignItems: "flex-end",
}));

export const MatrixTitle = styled(Typography)(() => ({
  fontSize: 20,
  fontWeight: 400,
  lineHeight: 1,
}));
