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

import { Accordion, Box, styled } from "@mui/material";
import DeleteIcon from "@mui/icons-material/HighlightOff";

export const ItemContainer = styled(Box, {
  shouldForwardProp: (prop) => prop !== "onTopVisible",
})<{ onTopVisible?: boolean }>(({ onTopVisible }) => ({
  display: "flex",
  justifyContent: "center",
  zIndex: onTopVisible ? 10000 : 9999,
  width: "100%",
  boxSizing: "border-box",
}));

export const DraggableAccorderon = styled(Accordion, {
  shouldForwardProp: (prop) => prop !== "isDragging",
})<{ isDragging?: boolean }>(({ theme, isDragging }) => ({
  flex: 1,
  boxSizing: "border-box",
  maxWidth: "800px",
  width: "100%",
  margin: "0 auto",
  ...(isDragging
    ? {
        borderColor: theme.palette.secondary.main,
        boxShadow: `0px 0px 2px rgb(8, 58, 30), 0px 0px 10px ${theme.palette.secondary.main}`,
      }
    : {
        margin: theme.spacing(0, 0.2),
      }),
}));

export const StyledDeleteIcon = styled(DeleteIcon)(({ theme }) => ({
  flex: "0 0 24px",
  color: theme.palette.error.light,
  margin: theme.spacing(0, 2),
  cursor: "pointer",
  alignSelf: "center",
  "&:hover": {
    color: theme.palette.error.main,
  },
}));

export const Info = styled(Box)(({ theme }) => ({
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  boxSizing: "border-box",
}));

export const Header = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "50px",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-end",
  alignItems: "center",
  boxSizing: "border-box",
  padding: theme.spacing(0, 1),
}));

export const JsonContainer = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  zIndex: 999, // for json edition modal to be up everything else
  maxHeight: "400px",
  maxWidth: "500px",
  overflow: "scroll",
}));

export const headerIconStyle = {
  width: "24px",
  height: "auto",
  cursor: "pointer",
  mx: 0.5,
  color: "primary.main",
  "&:header": {
    color: "primary.dark",
  },
};

export const detailsStyle = {
  width: "100%",
  height: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  boxSizing: "border-box",
};

export default {};
