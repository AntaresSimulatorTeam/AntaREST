import { useEffect, useState } from "react";
import { ColorResult, MaterialPicker } from "react-color";
import { Box, TextField, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import { LinkElement, UpdateAreaUi } from "../../../../../../../common/types";
import AreaLinks from "./AreaLinks";

import AreaLink from "./AreaLink";

import { AreaColorPicker, AreaHuePicker } from "../style";
import DeleteAreaDialog from "./DeleteAreaDialog";
import { AreaNode } from "../../../../../../../redux/ducks/studyMaps";

interface Props {
  node?: AreaNode;
  updateUI: (id: string, value: UpdateAreaUi) => void;
  currentLink?: LinkElement;
  currentArea?: AreaNode | undefined;
}

function AreaConfig(props: Props) {
  const [t] = useTranslation();
  const { node, updateUI, currentLink, currentArea } = props;
  const [currentColor, setCurrentColor] = useState<string>(node?.color || "");

  useEffect(() => {
    if (currentArea?.color) {
      setCurrentColor(currentArea.color);
    }
  }, [currentArea]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChangeColor = (color: ColorResult) => {
    if (currentArea) {
      setCurrentColor(`rgb(${color.rgb.r}, ${color.rgb.g}, ${color.rgb.b})`);
      updateUI(currentArea.id, {
        x: currentArea.x,
        y: currentArea.y,
        color_rgb:
          color.rgb !== null
            ? [color.rgb.r, color.rgb.g, color.rgb.b]
            : currentArea.color.slice(4, -1).split(",").map(Number),
      });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        flexGrow: 1,
        mb: 1,
      }}
    >
      {currentArea && (
        <Box
          sx={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            mt: 1,
            mb: 3,
          }}
        >
          <TextField
            sx={{ mt: 1 }}
            label={t("study.modelization.map.areaName")}
            variant="filled"
            value={currentArea.name}
            disabled
          />
          <AreaHuePicker
            color={currentColor}
            onChangeComplete={(color) => handleChangeColor(color)}
          />
          <AreaColorPicker>
            <MaterialPicker
              color={currentColor}
              onChangeComplete={(color) => handleChangeColor(color)}
            />
          </AreaColorPicker>
        </Box>
      )}
      {currentArea && <AreaLinks />}
      {currentLink && <AreaLink currentLink={currentLink} />}
      <Divider sx={{ height: "1px", width: "90%", mt: 1, mb: 1.5 }} />
      <DeleteAreaDialog currentArea={currentArea} currentLink={currentLink} />
    </Box>
  );
}

export default AreaConfig;
