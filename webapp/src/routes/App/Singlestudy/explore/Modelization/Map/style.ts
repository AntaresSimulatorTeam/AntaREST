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

import { styled, Box, Chip } from "@mui/material";
import mapbackground from "../../../../../../assets/img/mapbackground.png";
import { getTextColor, type RGB } from "./utils";

////////////////////////////////////////////////////////////////
// Map
////////////////////////////////////////////////////////////////

export const MapContainer = styled(Box)(() => ({
  width: "100%",
  height: "100%",
  position: "relative",
  '& svg[name="svg-container-graph-id"]': {
    backgroundImage: `url("${mapbackground}")`,
  },
  overflow: "hidden",
}));

export const MapHeader = styled(Box)(() => ({
  width: "100%",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  position: "absolute",
  top: "10px",
}));

////////////////////////////////////////////////////////////////
// Node
////////////////////////////////////////////////////////////////

export const NodeContainer = styled(Box)(() => ({
  width: "100%",
  height: "100%",
  display: "flex",
  padding: "4px",
  marginTop: "2px",
  marginLeft: "2px",
}));

export interface NodeProps {
  nodecolor: string;
  rgbcolor: number[];
}

export const NodeDefault = styled(Chip)<NodeProps>(({ theme, nodecolor, rgbcolor }) => ({
  backgroundColor: nodecolor,
  "&:hover": {
    color: "white",
    "& .MuiChip-deleteIcon": {
      color: "white",
      display: "block",
    },
  },
  "& .MuiChip-deleteIcon": {
    display: "none",
    fontSize: 20,
    marginLeft: 5,
    "&:hover": {
      color: theme.palette.primary.main,
    },
  },
  "& .MuiChip-label": {
    textOverflow: "unset",
  },
  color: getTextColor(rgbcolor as RGB),
}));

export const NodeHighlighted = styled(Chip)<NodeProps>(({ nodecolor, rgbcolor }) => ({
  color: getTextColor(rgbcolor as RGB),
  backgroundColor: `rgba(${rgbcolor[0]}, ${rgbcolor[1]}, ${rgbcolor[2]}, 0.6) !important`,
  outline: `2px dashed ${nodecolor}`,
}));
