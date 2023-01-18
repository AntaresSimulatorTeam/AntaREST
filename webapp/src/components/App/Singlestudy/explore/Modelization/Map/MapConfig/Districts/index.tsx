import { Box, Button } from "@mui/material";
import AutoSizer from "react-virtualized-auto-sizer";
import { useMemo, useState } from "react";
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

  const columns = useMemo(
    () => Object.keys(districts).map((id) => id),
    [districts]
  );

  const defaultValues = useMemo(
    () =>
      areas.reduce((acc: Record<string, Record<string, boolean>>, area) => {
        acc[area.id] = Object.values(districts).reduce(
          (acc2: Record<string, boolean>, district) => {
            acc2[district.id] = !!district.areas.includes(area.id);
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

  const handleSubmit = (data: SubmitHandlerPlus) => {
    const areasByDistrict: Record<string, string[]> = {};

    Object.keys(data.dirtyValues).forEach((areaId) => {
      Object.keys(data.dirtyValues[areaId] || {}).forEach((districtId) => {
        areasByDistrict[districtId] ||= [...districts[districtId].areas];

        if (data.dirtyValues[areaId]?.[districtId]) {
          areasByDistrict[districtId].push(areaId);
        } else {
          areasByDistrict[districtId] = areasByDistrict[districtId].filter(
            (id) => id !== areaId
          );
        }
      });
    });

    const promises = Object.keys(areasByDistrict).map((districtId) => {
      return dispatch(
        updateStudyMapDistrict({
          studyId: study.id,
          districtId,
          output: districts[districtId].output,
          areas: areasByDistrict[districtId],
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
          Edit Districts
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
                    colHeaders: (_, colName) => districts[colName].name,
                    selectionMode: "single",
                  }}
                  onSubmit={handleSubmit}
                />
              </Box>
            )}
          </AutoSizer>
        )}
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
