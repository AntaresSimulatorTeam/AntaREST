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

import DataGridForm from "@/components/DataGridForm";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useStudy from "@/routes/-shared/hook/useStudy";
import type { GridColumn } from "@glideapps/glide-data-grid";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import { Box, Button } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { updateStudyMapDistrict } from "../../../../../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../../../../../redux/hooks/useAppSelector";
import { getAreas, getStudyMapDistrictsById } from "../../../../../../../../../../redux/selectors";
import CreateDistrictDialog from "./CreateDistrictDialog";
import UpdateDistrictDialog from "./UpdateDistrictDialog";

function Districts() {
  const study = useStudy();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const districtsById = useAppSelector(getStudyMapDistrictsById);
  const [createDistrictDialogOpen, setCreateDistrictDialogOpen] = useState(false);
  const [updateDistrictDialogOpen, setUpdateDistrictDialogOpen] = useState(false);

  const columns = useMemo<Array<GridColumn & { id: string }>>(
    () =>
      Object.keys(districtsById).map((id) => ({
        id,
        title: districtsById[id].name,
      })),
    [districtsById],
  );

  const defaultData = useMemo(() => {
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
          // remove-all is hard coded here
          // The front always send updates with apply filter set to remove-all
          applyFilter: "remove-all",
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
          {t("study.modeling.map.districts.add")}
        </Button>
        <Button
          color="primary"
          variant="outlined"
          startIcon={<EditIcon />}
          onClick={() => setUpdateDistrictDialogOpen(true)}
        >
          {t("study.modeling.map.districts.edit")}
        </Button>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: "hidden" }}>
        {columns.length > 0 && (
          <DataGridForm
            key={JSON.stringify(defaultData)}
            defaultData={defaultData}
            columns={columns}
            onSubmit={handleSubmit}
            rowMarkers={{
              kind: "clickable-string",
              getTitle: (index) => areas[index].name,
              width: 150,
            }}
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
