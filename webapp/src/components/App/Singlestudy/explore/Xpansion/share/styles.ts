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

import DeleteIcon from "@mui/icons-material/Delete";
import VisibilityIcon from "@mui/icons-material/Visibility";
import { Box, Button, styled, Typography } from "@mui/material";

export const Fields = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "center",
  width: "100%",
  flexWrap: "wrap",
  marginBottom: theme.spacing(2),
  "&> div": {
    width: "270px",
    marginRight: theme.spacing(2),
  },
}));

export const SelectFields = styled(Box)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  width: "300px",
  marginRight: "50px",
}));

export const Title = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.primary,
  fontSize: "1.25rem",
  fontWeight: 400,
  lineHeight: 1.334,
}));

export const HoverButton = styled(Button)(({ theme }) => ({
  color: theme.palette.action.active,
  borderColor: theme.palette.text.disabled,
  "&:hover": {
    backgroundColor: "rgba(255,255,255,0.11)",
    borderColor: theme.palette.text.primary,
    color: theme.palette.text.primary,
  },
}));

export const ActiveButton = styled(Button)(({ theme }) => ({
  backgroundColor: `${theme.palette.secondary.main} !important`,
  color: `white !important`,
  borderColor: `${theme.palette.secondary.main} !important`,
}));

export const StyledVisibilityIcon = styled(VisibilityIcon)(({ theme }) => ({
  marginLeft: theme.spacing(1),
  marginRight: theme.spacing(1),
  color: theme.palette.action.active,
  "&:hover": {
    color: "white",
    cursor: "pointer",
  },
}));

export const StyledDeleteIcon = styled(DeleteIcon)(({ theme }) => ({
  cursor: "pointer",
  color: theme.palette.error.light,
  "&:hover": {
    color: theme.palette.error.main,
  },
}));

export default {};
