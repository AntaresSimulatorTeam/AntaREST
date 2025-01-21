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

import { Box, Button, styled } from "@mui/material";

export const Code = styled(Box)({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
  padding: "8px",
  overflow: "auto",
});

export const StyledButton = styled(Button)(({ theme }) => ({
  backgroundColor: "rgba(180, 180, 180, 0.09)",
  color: "white",
  borderRight: "none !important",
  "&:hover": {
    color: "white",
    backgroundColor: theme.palette.secondary.main,
  },
  "&:disabled": {
    backgroundColor: theme.palette.secondary.dark,
    color: "white !important",
  },
}));
