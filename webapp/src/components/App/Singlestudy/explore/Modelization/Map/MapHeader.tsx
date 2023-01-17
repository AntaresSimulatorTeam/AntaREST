import { Box, Chip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { LinkProperties } from "../../../../../../common/types";
import {
  StudyMapNode,
  setCurrentLayer,
} from "../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import {
  getCurrentLayer,
  getStudyMapLayers,
} from "../../../../../../redux/selectors";

interface Props {
  links: LinkProperties[];
  nodes: StudyMapNode[];
}

function MapHeader(props: Props) {
  const { nodes, links } = props;
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const layers = useAppSelector(getStudyMapLayers);
  const currentLayerId = useAppSelector(getCurrentLayer);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleLayerClick = (layerId: string) => {
    dispatch(setCurrentLayer(layerId));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        position: "absolute",
        padding: "10px",
        backdropFilter: "blur(2px)",
      }}
    >
      <Box
        sx={{
          display: "flex",
          width: "80%",
          flexWrap: "wrap",
        }}
      >
        {Object.values(layers).map(({ id, name }) => (
          <Chip
            key={id}
            label={name}
            color={currentLayerId === id ? "secondary" : "default"}
            clickable
            size="small"
            sx={{ m: 1 }}
            onClick={() => handleLayerClick(id)}
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
