import { styled, Box, Chip } from "@mui/material";
import mapbackground from "../../../../../../assets/mapbackground.png";
import { getTextColor, RGB } from "./utils";

////////////////////////////////////////////////////////////////
// Map(index.tsx)
////////////////////////////////////////////////////////////////

export const MapContainer = styled(Box)(() => ({
  width: "100%",
  height: "100%",
  position: "relative",
  '& svg[name="svg-container-graph-id"]': {
    backgroundImage: `url("${mapbackground}")`,
  },
}));

export const MapHeader = styled(Box)(() => ({
  width: "14%",
  display: "flex",
  justifyContent: "space-around",
  alignItems: "center",
  position: "absolute",
  right: "16px",
  top: "10px",
}));

export const MapFooter = styled(Box)(() => ({
  position: "absolute",
  right: "15px",
  bottom: "15px",
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

export type NodeProps = {
  nodecolor: string;
  rgbcolor: number[];
};

export const NodeDefault = styled(Chip)<NodeProps>(
  ({ theme, nodecolor, rgbcolor }) => ({
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
  })
);

export const NodeHighlighted = styled(Chip)<NodeProps>(
  ({ nodecolor, rgbcolor }) => ({
    color: getTextColor(rgbcolor as RGB),
    backgroundColor: `rgba(${rgbcolor[0]}, ${rgbcolor[1]}, ${rgbcolor[2]}, 0.6)`,
    outline: `2px dashed ${nodecolor}`,
  })
);
