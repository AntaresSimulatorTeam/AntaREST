import { Box, Button } from "@mui/material";
import AutoSizer from "react-virtualized-auto-sizer";
import { useState } from "react";
import { useOutletContext } from "react-router";
import { Add, Edit } from "@mui/icons-material";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getStudyMapDistricts,
} from "../../../../../../../../redux/selectors";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import FormTable from "../../../../../../../common/FormTable";
import CreateDistrictDialog from "./CreateDistrictDialog";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import { updateStudyMapDistrict } from "../../../../../../../../redux/ducks/studyMaps";
import UpdateDistrictDialog from "./UpdateDistrictDialog";

function Districts() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const districts = useAppSelector(getStudyMapDistricts);
  const [createDistrictDialogOpen, setCreateDistrictDialogOpen] =
    useState(false);
  const [updateDistrictDialogOpen, setUpdateDistrictDialogOpen] =
    useState(false);

  const combinedDistricts = areas.map((area) => ({
    [area.id]: Object.values(districts).reduce((acc, { name, areas }) => {
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      acc[name] = !!areas.includes(area.id);
      return acc;
    }, {}),
  }));

  const mapDistricts = Object.assign({}, ...combinedDistricts);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus) => {
    const areaId = Object.keys(data.dirtyValues)[0];
    const districtName = Object.keys(data.dirtyValues[areaId]).find(
      (district) => district
    );
    if (districtName) {
      const districtAreas = Object.keys(data.values).filter(
        (area) => data.values[area][districtName]
      );
      const targetDistrict = Object.values(districts).find(
        (district) => district.name === districtName
      );
      if (targetDistrict) {
        dispatch(
          updateStudyMapDistrict({
            studyId: study.id,
            districtId: targetDistrict.id,
            output: targetDistrict.output,
            areas: districtAreas,
          })
        );
      }
    }
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
          onClick={() => setUpdateDistrictDialogOpen(true)}
        >
          Edit District
        </Button>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: "hidden" }}>
        <AutoSizer>
          {({ height, width }) => (
            <Box sx={{ height, width, position: "relative" }}>
              <FormTable
                key={JSON.stringify(districts)}
                defaultValues={mapDistricts}
                onSubmit={handleSubmit}
              />
            </Box>
          )}
        </AutoSizer>
      </Box>

      {createDistrictDialogOpen && (
        <CreateDistrictDialog
          open={createDistrictDialogOpen}
          onClose={() => setCreateDistrictDialogOpen(false)}
        />
      )}
      {updateDistrictDialogOpen && (
        <UpdateDistrictDialog
          open={updateDistrictDialogOpen}
          onClose={() => setUpdateDistrictDialogOpen(false)}
        />
      )}
    </Box>
  );
}

export default Districts;
