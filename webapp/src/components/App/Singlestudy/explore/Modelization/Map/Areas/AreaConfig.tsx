import { useEffect, useState } from "react";
import { ColorResult, MaterialPicker } from "react-color";
import { Box, TextField, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import { LinkElement, UpdateAreaUi } from "../../../../../../../common/types";
import AreaLinks from "./AreaLinks";

import AreaLink from "./AreaLink";

import { AreaColorPicker, AreaHuePicker } from "./style";
import DeleteAreaDialog from "./DeleteAreaDialog";
import { StudyMapNode } from "../../../../../../../redux/ducks/studyMaps";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentLayer } from "../../../../../../../redux/selectors";

interface Props {
  node?: StudyMapNode;
  updateUI: (id: string, value: UpdateAreaUi) => void;
  currentLink?: LinkElement;
  currentArea?: StudyMapNode | undefined;
}

function AreaConfig(props: Props) {
  const [t] = useTranslation();
  const { node, updateUI, currentLink, currentArea } = props;
  const currentLayerId = useAppSelector(getCurrentLayer);
  const [currentColor, setCurrentColor] = useState(node?.color || "");

  useEffect(() => {
    if (currentArea?.layerColor) {
      setCurrentColor(`rgb(${currentArea.layerColor[currentLayerId]})`);
    }
  }, [currentArea?.layerColor, currentLayerId]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChangeColor = (color: ColorResult) => {
    const { r, g, b } = color.rgb;
    if (currentArea) {
      const { id, x, y, layerX, layerY, layerColor } = currentArea;
      setCurrentColor(`rgb(${layerColor[currentLayerId]})`);
      updateUI(id, {
        x,
        y,
        layerX,
        layerY,
        layerColor,
        color_rgb:
          color.rgb !== null
            ? [r, g, b]
            : currentArea.layerColor[currentLayerId].split(",").map(Number),
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
