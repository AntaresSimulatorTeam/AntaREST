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

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "center",
  alignItems: "center",
  padding: 0,
}));

export const Container = styled(List)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "center",
  alignItems: "center",
}));

export const FilterLinkContainer = styled(List)(({ theme }) => ({
  display: "flex",
  width: "100%",
  border: 0,
  flexFlow: "row wrap",
  justifyContent: "flex-start",
  alignItems: "center",
  listStyle: "none",
  padding: theme.spacing(0.5),
  marginTop: theme.spacing(1),
  margin: 0,
}));

export default {};
