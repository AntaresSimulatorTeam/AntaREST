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

import { Box, List, styled } from "@mui/material";
import AddCircleOutlinedIcon from "@mui/icons-material/AddCircleOutlined";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  padding: 0,
  marginBottom: 0,
}));

export const InputContainer = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: 0,
  marginBottom: theme.spacing(1),
}));

export const TagContainer = styled(List)(({ theme }) => ({
  display: "flex",
  flexDirection: "row",
  width: "100%",
  border: 0,
  justifyContent: "flex-start",
  flexWrap: "wrap",
  listStyle: "none",
  padding: theme.spacing(0.5),
  margin: 0,
}));

export const AddIcon = styled(AddCircleOutlinedIcon)(({ theme }) => ({
  color: theme.palette.primary.main,
  margin: theme.spacing(0, 1),
  cursor: "pointer",
  "&:hover": {
    color: theme.palette.primary.dark,
  },
}));

export default {};
