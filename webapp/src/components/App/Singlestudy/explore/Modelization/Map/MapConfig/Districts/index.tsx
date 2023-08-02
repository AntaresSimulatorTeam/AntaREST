import { Box, Button } from "@mui/material";
import { useMemo, useState } from "react";
import { useOutletContext } from "react-router";
import { Add, Edit } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getStudyMapDistrictsById,
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
  const [t] = useTranslation();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const districtsById = useAppSelector(getStudyMapDistrictsById);
  const [createDistrictDialogOpen, setCreateDistrictDialogOpen] =
    useState(false);
  const [updateDistrictDialogOpen, setUpdateDistrictDialogOpen] =
    useState(false);

  const columns = useMemo(
    () => Object.keys(districtsById).map((id) => id),
    [districtsById]
  );

  const defaultValues = useMemo(
    () =>
      areas.reduce((acc: Record<string, Record<string, boolean>>, area) => {
        acc[area.id] = Object.values(districtsById).reduce(
          (acc2: Record<string, boolean>, district) => {
            acc2[district.id] = !!district.areas.includes(area.id);
            return acc2;
          },
          {}
        );
        return acc;
      }, {}),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [columns.length, areas]
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus) => {
    const areasByDistrict: Record<string, string[]> = {};

    Object.keys(data.dirtyValues).forEach((areaId) => {
      Object.keys(data.dirtyValues[areaId] || {}).forEach((districtId) => {
        areasByDistrict[districtId] ||= [...districtsById[districtId].areas];

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
          output: districtsById[districtId].output,
          comments: districtsById[districtId].comments,
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
          {t("study.modelization.map.districts.add")}
        </Button>
        <Button
          color="primary"
          variant="outlined"
          size="small"
          startIcon={<Edit />}
          onClick={() => setUpdateDistrictDialogOpen(true)}
        >
          {t("study.modelization.map.districts.edit")}
        </Button>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: "hidden" }}>
        {columns.length > 0 && (
          <FormTable
            key={JSON.stringify(defaultValues)}
            defaultValues={defaultValues}
            tableProps={{
              columns,
              colHeaders: (_, colName) => districtsById[colName].name,
              selectionMode: "single",
            }}
            onSubmit={handleSubmit}
          />
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
