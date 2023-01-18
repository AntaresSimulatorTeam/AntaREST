import { Box, Button } from "@mui/material";
import AutoSizer from "react-virtualized-auto-sizer";
import { useMemo, useState } from "react";
import { useOutletContext } from "react-router";
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
import { updateStudyMapLayer } from "../../../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";

function Layers() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const layers = useAppSelector(getStudyMapLayers);
  const [createLayerDialogOpen, setCreateLayerDialogOpen] = useState(false);
  const [editLayerDialogOpen, setEditLayerDialogOpen] = useState(false);

  const defaultValues = useMemo(
    () =>
      areas.reduce((acc: Record<string, Record<string, boolean>>, area) => {
        acc[area.id] = Object.values(layers).reduce(
          (acc2: Record<string, boolean>, layer) => {
            acc2[layer.id] = !!layer.areas.includes(area.id);
            return acc2;
          },
          {}
        );
        return acc;
      }, {}),
    [areas, layers]
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    try {
      const areasByLayer: Record<string, string[]> = {};

      Object.keys(data.dirtyValues).forEach((areaId) => {
        Object.keys(data.dirtyValues[areaId] || {}).forEach((layerId) => {
          areasByLayer[layerId] ||= layers[layerId].areas;
          if (data.dirtyValues[areaId]?.[layerId]) {
            areasByLayer[layerId].push(areaId);
          } else {
            areasByLayer[layerId] = areasByLayer[layerId].filter(
              (id) => id !== areaId
            );
          }
        });
      });

      console.log("areasByLayer :>> ", areasByLayer);

      const promises = Object.keys(areasByLayer).map((layerId) => {
        console.log("args", {
          studyId: study.id,
          layerId,
          name: layers[layerId].name,
          areas: areasByLayer[layerId],
        });
        return dispatch(
          updateStudyMapLayer({
            studyId: study.id,
            layerId,
            name: layers[layerId].name,
            areas: areasByLayer[layerId],
          })
        ).unwrap();
      });

      return Promise.all(promises);
    } catch (e) {
      console.error(e);
    }
  };

  /*    
        const layerName = Object.keys(data.dirtyValues[areaName]).find(
          (layer) => layer
        );

        const layerAreas = Object.keys(data.values).filter(
          (area) => data.values[area][layerName || ""]
        );

        console.log("layerAreas", layerAreas);
        const targetLayer = Object.values(layers).find(
          (layer) => layer.name === layerName
        );

        if (targetLayer && layerName) {
          const promise = dispatch(
            updateStudyMapLayer({
              studyId: study.id,
              layerId: targetLayer.id,
              name: layerName,
              areas: layerAreas,
            })
          ).unwrap();

          promises.push(promise);
        } */

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box sx={{ mb: 2 }}>
        <Button
          color="primary"
          variant="outlined"
          size="small"
          startIcon={<Add />}
          onClick={() => setCreateLayerDialogOpen(true)}
          sx={{ mr: 1 }}
        >
          Add Layer
        </Button>
        <Button
          color="primary"
          variant="outlined"
          size="small"
          startIcon={<Edit />}
          onClick={() => setEditLayerDialogOpen(true)}
        >
          Edit Layers
        </Button>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: "hidden" }}>
        <AutoSizer>
          {({ height, width }) => (
            <Box sx={{ height, width, position: "relative" }}>
              <FormTable
                key={JSON.stringify(defaultValues)}
                defaultValues={defaultValues}
                tableProps={{
                  colHeaders: (_, colName) => layers[colName].name,
                }}
                onSubmit={handleSubmit}
              />
            </Box>
          )}
        </AutoSizer>
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
