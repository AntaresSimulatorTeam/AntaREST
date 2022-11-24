import { useEffect, useState } from "react";
import { ColorResult, MaterialPicker } from "react-color";
import { Box, TextField, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import {
  NodeProperties,
  UpdateAreaUi,
} from "../../../../../../../common/types";
import AreaLinks from "./AreaLinks";

import AreaLink from "./AreaLink";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import {
  getSelectedLink,
  getSelectedNode,
} from "../../../../../../../redux/selectors";
import { AreaColorPicker, AreaHuePicker } from "../style";
import DeleteAreaDialog from "./DeleteAreaDialog";

interface Props {
  node?: NodeProperties;
  updateUI: (id: string, value: UpdateAreaUi) => void;
}

function AreaConfig(props: Props) {
  const [t] = useTranslation();
  const { node, updateUI } = props;
  const [currentColor, setCurrentColor] = useState<string>(node?.color || "");
  const selectedNode = useAppSelector(getSelectedNode);
  const selectedLink = useAppSelector(getSelectedLink);

  useEffect(() => {
    if (selectedNode?.color) {
      setCurrentColor(selectedNode.color);
    }
  }, [selectedNode]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChangeColor = (color: ColorResult) => {
    if (selectedNode) {
      setCurrentColor(`rgb(${color.rgb.r}, ${color.rgb.g}, ${color.rgb.b})`);
      updateUI(selectedNode.id, {
        x: selectedNode.x,
        y: selectedNode.y,
        color_rgb:
          color.rgb !== null
            ? [color.rgb.r, color.rgb.g, color.rgb.b]
            : selectedNode.color.slice(4, -1).split(",").map(Number),
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
      {selectedNode && (
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
            value={selectedNode.name}
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
      {selectedNode && <AreaLinks />}
      {selectedLink && <AreaLink />}
      <Divider sx={{ height: "1px", width: "90%", mt: 1, mb: 1.5 }} />
      <DeleteAreaDialog />
    </Box>
  );
}

export default AreaConfig;
