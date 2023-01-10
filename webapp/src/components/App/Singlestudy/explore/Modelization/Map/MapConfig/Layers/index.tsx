import { Box, Button } from "@mui/material";
import { useState } from "react";
import { useOutletContext } from "react-router";
import { useTranslation } from "react-i18next";
import { Add, Edit } from "@mui/icons-material";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getStudyMapLayers,
} from "../../../../../../../../redux/selectors";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import FormTable from "../../../../../../../common/FormTable";
import CreateLayerDialog from "./CreateLayerDialog";
import EditLayerDialog from "./EditLayerDialog";
import {
  StudyMapNode,
  updateStudyMapLayer,
} from "../../../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";

function Layers() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const layers = useAppSelector(getStudyMapLayers);
  const [createLayerDialogOpen, setCreateLayerDialogOpen] = useState(false);
  const [editLayerDialogOpen, setEditLayerDialogOpen] = useState(false);

  const combinedLayers = areas.map((area) => ({
    [area.id]: Object.values(layers).reduce((acc, { name, areas }) => {
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      acc[name] = !!areas.includes(area.id);
      return acc;
    }, {}),
  }));

  const mapLayers = Object.assign({}, ...combinedLayers);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus) => {
    if (data) {
      const areaName = Object.keys(data.dirtyValues)[0];
      const layerName = Object.keys(data.dirtyValues[areaName]).find(
        (layer) => layer
      );
      const layerAreas = Object.keys(data.values).filter(
        (area) => data.values[area][layerName || ""]
      ) as unknown as StudyMapNode[];
      const targetLayer = Object.values(layers).find(
        (layer) => layer.name === layerName
      );
      if (targetLayer && layerName) {
        dispatch(
          updateStudyMapLayer({
            studyId: study.id,
            layerId: targetLayer.id,
            name: layerName,
            areas: layerAreas,
          })
        );
      }
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ width: "100%", height: "100%", py: 3 }}>
      <Box sx={{ mb: 2 }}>
        <Button
          color="primary"
          variant="outlined"
          size="small"
          startIcon={<Add />}
          onClick={() => setCreateLayerDialogOpen(true)}
          sx={{ mr: 1 }}
        >
          {t("Add Layer")}
        </Button>
        <Button
          color="primary"
          variant="outlined"
          size="small"
          startIcon={<Edit />}
          onClick={() => setEditLayerDialogOpen(true)}
        >
          {t("Edit Layers")}
        </Button>
      </Box>
      <Box>
        <FormTable
          key={JSON.stringify(layers)}
          defaultValues={mapLayers}
          onSubmit={handleSubmit}
        />
      </Box>
      {createLayerDialogOpen && (
        <CreateLayerDialog
          open={createLayerDialogOpen}
          onClose={() => setCreateLayerDialogOpen(false)}
        />
      )}
      {editLayerDialogOpen && (
        <EditLayerDialog
          open={editLayerDialogOpen}
          onClose={() => setEditLayerDialogOpen(false)}
        />
      )}
    </Box>
  );
}

export default Layers;
