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

import { Box, StepConnector, stepConnectorClasses, styled } from "@mui/material";

export const QontoConnector = styled(StepConnector)(({ theme }) => ({
  [`&.${stepConnectorClasses.disabled}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      height: "auto",
    },
  },
}));

export const QontoStepIconRoot = styled("div")(({ theme }) => [
  {
    color: "#eaeaf0",
    display: "flex",
    width: "24px",
    justifyContent: "center",
    alignItems: "center",
    "& .QontoStepIcon-inprogress": {
      width: 16,
      height: 16,
      color: theme.vars.palette.primary.main,
    },
  },
  theme.applyStyles("dark", {
    color: theme.vars.palette.grey[700],
  }),
]);

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
