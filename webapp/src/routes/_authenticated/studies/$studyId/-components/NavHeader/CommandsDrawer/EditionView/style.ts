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

export const Root = styled(Box)(() => ({
  width: "100%",
  height: "98%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  overflowY: "auto",
}));

export const Header = styled(Box)(() => ({
  width: "95%",
  height: "80px",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "space-between",
  alignItems: "center",
}));

export const EditHeader = styled(Box)(() => ({
  flex: 1,
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-end",
  alignItems: "center",
}));

export const Body = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "center",
  overflow: "auto",
  boxSizing: "border-box",
  position: "relative",
  padding: theme.spacing(0, 2),
}));

export const headerIconStyle = {
  width: "24px",
  height: "auto",
  cursor: "pointer",
  color: "primary.main",
  mx: 2,
  "&:hover": {
    color: "primary.dark",
  },
};

export default {};
