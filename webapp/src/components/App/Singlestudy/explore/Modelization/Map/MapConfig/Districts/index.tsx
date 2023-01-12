import { Box, Button } from "@mui/material";
import { useState } from "react";
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
import CreateDistrictDialog from "./CreateDistrictDialog";
import EditDistrictDialog from "./EditDistrictDialog";

function Districts() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const layers = useAppSelector(getStudyMapLayers);
  const [createDistrictDialogOpen, setCreateDistrictDialogOpen] =
    useState(false);
  const [editDistrictDialogOpen, setEditDistrictDialogOpen] = useState(false);

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
    console.log("data :>> ", data);
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
          onClick={() => setCreateDistrictDialogOpen(true)}
          sx={{ mr: 1 }}
        >
          Add District
        </Button>
        <Button
          color="primary"
          variant="outlined"
          size="small"
          startIcon={<Edit />}
          onClick={() => setEditDistrictDialogOpen(true)}
        >
          Edit District
        </Button>
      </Box>
      <Box>
        <FormTable
          key={JSON.stringify(layers)}
          defaultValues={mapLayers}
          onSubmit={handleSubmit}
        />
      </Box>
      {createDistrictDialogOpen && (
        <CreateDistrictDialog
          open={createDistrictDialogOpen}
          onClose={() => setCreateDistrictDialogOpen(false)}
        />
      )}
      {editDistrictDialogOpen && (
        <EditDistrictDialog
          open={editDistrictDialogOpen}
          onClose={() => setEditDistrictDialogOpen(false)}
        />
      )}
    </Box>
  );
}

export default Districts;
