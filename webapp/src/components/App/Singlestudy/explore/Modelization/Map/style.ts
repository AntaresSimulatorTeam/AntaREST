import { styled, Box, Chip, Typography } from "@mui/material";
import { HuePicker } from "react-color";
import DeleteIcon from "@mui/icons-material/Delete";
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

////////////////////////////////////////////////////////////////
// Areas
////////////////////////////////////////////////////////////////

export const AreasContainer = styled(Box)(() => ({
  width: "100%",
  flexGrow: 1,
  flexShrink: 1,
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
  overflowY: "auto",
}));

export const AreaHuePicker = styled(HuePicker)(({ theme }) => ({
  width: "90% !important",
  margin: theme.spacing(1),
}));

export const AreaColorPicker = styled(Box)(({ theme }) => ({
  "& > div > div:first-of-type": {
    backgroundColor: "rgba(0, 0, 0, 0.12) !important",
    boxShadow: "none !important",
  },
  "& > div > div:last-of-type > div": {
    width: "unset !important",
    height: "120px !important",
    maxWidth: "275px !important",
    fontFamily: '"Inter", sans-serif !important',
    boxShadow: "none",
    "& > div > input, > div > div > div > input": {
      backgroundColor: "rgba(0,0,0,0)",
      color: `${theme.palette.text.secondary} !important`,
    },
  },
}));

export const AreaDeleteIcon = styled(DeleteIcon)(({ theme }) => ({
  cursor: "pointer",
  color: theme.palette.error.light,
  "&:hover": {
    color: theme.palette.error.main,
  },
}));

export const AreaLinkRoot = styled(Typography)(() => ({
  width: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
}));

export const AreaLinkTitle = styled(Typography)(({ theme }) => ({
  width: "90%",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  color: theme.palette.text.secondary,
  fontWeight: "bold",
}));

export const AreaLinkContainer = styled(Typography)(() => ({
  width: "90%",
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "baseline",
  boxSizing: "border-box",
}));

export const AreaLinkLabel = styled(Typography)(({ theme }) => ({
  fontWeight: "bold",
  color: theme.palette.text.secondary,
}));

export const AreaLinkContent = styled(Typography)(({ theme }) => ({
  cursor: "pointer",
  color: theme.palette.text.secondary,
  padding: theme.spacing(1.5),
  fontSize: 18,
  "&:hover": {
    textDecoration: "underline",
    color: "white",
  },
}));
