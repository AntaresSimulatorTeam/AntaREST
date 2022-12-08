import { Box, Chip, Typography } from "@mui/material";
import { SetStateAction, useState } from "react";
import { useTranslation } from "react-i18next";
import { LinkProperties } from "../../../../../../common/types";
import {
  AreaNode,
  setCurrentLayer,
} from "../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getStudyMapLayers } from "../../../../../../redux/selectors";

interface Props {
  links: LinkProperties[];
  nodes: AreaNode[];
}
function MapHeader(props: Props) {
  const { nodes, links } = props;
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const layers = useAppSelector(getStudyMapLayers);
  const [activeLayer, setActiveLayer] = useState(layers[0].name);

  const handleLayerClick = (
    layerId: string,
    layerName: SetStateAction<string>
  ) => {
    dispatch(setCurrentLayer(layerId));
    setActiveLayer(layerName);
  };

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        position: "absolute",
        padding: "10px",
      }}
    >
      <Box
        sx={{
          display: "flex",
          width: "80%",
        }}
      >
        {layers &&
          Object.values(layers).map(({ id, name }) => (
            <Chip
              key={id}
              label={name}
              color={activeLayer === name ? "secondary" : "default"}
              clickable
              size="small"
              sx={{ mx: 1 }}
              onClick={() => handleLayerClick(id, name)}
            />
          ))}
      </Box>
      <Box
        sx={{
          display: "flex",
        }}
      >
        <Typography sx={{ mx: 1 }}>{`${nodes.length} ${t(
          "study.areas"
        )}`}</Typography>
        <Typography sx={{ mx: 1 }}>{`${links.length} ${t(
          "study.links"
        )}`}</Typography>
      </Box>
    </Box>
  );
}

export default MapHeader;
