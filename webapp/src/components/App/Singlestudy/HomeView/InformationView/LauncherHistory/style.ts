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

import { Box, StepConnector, stepConnectorClasses, styled } from "@mui/material";

export const JobRoot = styled(Box, {
  shouldForwardProp: (prop) => prop !== "jobLength",
})<{ jobLength: number }>(({ theme, jobLength }) => ({
  width: "100%",
  flex: 1,
  display: "flex",
  justifyContent: jobLength > 0 ? "flex-start" : "center",
  alignItems: jobLength > 0 ? "flex-start" : "center",
  overflowX: "hidden",
  overflowY: "auto",
}));

export const QontoConnector = styled(StepConnector)(({ theme }) => ({
  [`&.${stepConnectorClasses.disabled}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      height: "auto",
    },
  },
}));

export const QontoStepIconRoot = styled("div")(({ theme }) => ({
  color: theme.palette.mode === "dark" ? theme.palette.grey[700] : "#eaeaf0",
  display: "flex",
  width: "24px",
  justifyContent: "center",
  alignItems: "center",
  "& .QontoStepIcon-inprogress": {
    width: 16,
    height: 16,
    color: theme.palette.primary.main,
  },
}));

export const StepLabelRoot = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
}));

export const StepLabelRow = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  justifyContent: "flex-start",
  boxSizing: "border-box",
}));

export const CancelContainer = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  height: "30px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: theme.spacing(1),
}));

export default {};
