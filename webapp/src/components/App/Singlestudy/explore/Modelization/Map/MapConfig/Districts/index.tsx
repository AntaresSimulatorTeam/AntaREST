/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { Box, Button } from "@mui/material";
import { useMemo, useState } from "react";
import { useOutletContext } from "react-router";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../../../types/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getAreas, getStudyMapDistrictsById } from "../../../../../../../../redux/selectors";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import TableForm from "../../../../../../../common/TableForm";
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
  const [createDistrictDialogOpen, setCreateDistrictDialogOpen] = useState(false);
  const [updateDistrictDialogOpen, setUpdateDistrictDialogOpen] = useState(false);

  const columns = useMemo(() => Object.keys(districtsById).map((id) => id), [districtsById]);

  const defaultValues = useMemo(() => {
    const districts = Object.values(districtsById);

    return areas.reduce(
      (acc, area) => {
        acc[area.id] = districts.reduce(
          (acc2, district) => {
            acc2[district.id] = district.areas.includes(area.id);
            return acc2;
          },
          {} as Record<string, boolean>,
        );

        return acc;
      },
      {} as Record<string, Record<string, boolean>>,
    );
  }, [areas, districtsById]);

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
          areasByDistrict[districtId] = areasByDistrict[districtId].filter((id) => id !== areaId);
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
        }),
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
          startIcon={<AddIcon />}
          onClick={() => setCreateDistrictDialogOpen(true)}
          sx={{ mr: 1 }}
        >
          {t("study.modelization.map.districts.add")}
        </Button>
        <Button
          color="primary"
          variant="outlined"
          startIcon={<EditIcon />}
          onClick={() => setUpdateDistrictDialogOpen(true)}
        >
          {t("study.modelization.map.districts.edit")}
        </Button>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: "hidden" }}>
        {columns.length > 0 && (
          <TableForm
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
