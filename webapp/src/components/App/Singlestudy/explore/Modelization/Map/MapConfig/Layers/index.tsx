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
import { updateStudyMapLayer } from "../../../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import UpdateLayerDialog from "./UpdateLayerDialog";

function Layers() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const layers = useAppSelector(getStudyMapLayers);
  const [createLayerDialogOpen, setCreateLayerDialogOpen] = useState(false);
  const [updateLayerDialogOpen, setUpdateLayerDialogOpen] = useState(false);

  const columns = useMemo(() => {
    return (
      Object.keys(layers)
        // Remove "All"
        .filter((id) => id !== "0")
        .map((id) => id)
    );
  }, [layers]);

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [columns.length]
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const areasByLayer: Record<string, string[]> = {};

    Object.keys(data.dirtyValues).forEach((areaId) => {
      Object.keys(data.dirtyValues[areaId] || {}).forEach((layerId) => {
        areasByLayer[layerId] ||= [...layers[layerId].areas];

        if (data.dirtyValues[areaId]?.[layerId]) {
          areasByLayer[layerId].push(areaId);
        } else {
          areasByLayer[layerId] = areasByLayer[layerId].filter(
            (id) => id !== areaId
          );
        }
      });
    });

    const promises = Object.keys(areasByLayer).map((layerId) => {
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
  };

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
          onClick={() => setUpdateLayerDialogOpen(true)}
        >
          Edit Layers
        </Button>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: "hidden" }}>
        {columns.length > 0 && (
          <AutoSizer>
            {({ height, width }) => (
              <Box sx={{ height, width, position: "relative" }}>
                <FormTable
                  key={JSON.stringify(defaultValues)}
                  defaultValues={defaultValues}
                  tableProps={{
                    columns,
                    colHeaders: (_, colName) => layers[colName].name,
                    selectionMode: "single",
                  }}
                  onSubmit={handleSubmit}
                />
              </Box>
            )}
          </AutoSizer>
        )}
      </Box>
      {createLayerDialogOpen && (
        <CreateLayerDialog
          open={createLayerDialogOpen}
          onClose={() => setCreateLayerDialogOpen(false)}
        />
      )}
      {updateLayerDialogOpen && (
        <UpdateLayerDialog
          open={updateLayerDialogOpen}
          onClose={() => setUpdateLayerDialogOpen(false)}
        />
      )}
    </Box>
  );
}

export default Layers;
