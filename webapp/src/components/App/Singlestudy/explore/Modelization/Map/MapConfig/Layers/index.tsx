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
import { getAreas, getStudyMapLayersById } from "../../../../../../../../redux/selectors";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import TableForm from "../../../../../../../common/TableForm";
import CreateLayerDialog from "./CreateLayerDialog";
import { updateStudyMapLayer } from "../../../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import UpdateLayerDialog from "./UpdateLayerDialog";

function Layers() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const layersById = useAppSelector(getStudyMapLayersById);
  const [createLayerDialogOpen, setCreateLayerDialogOpen] = useState(false);
  const [updateLayerDialogOpen, setUpdateLayerDialogOpen] = useState(false);

  const columns = useMemo(() => {
    return (
      Object.keys(layersById)
        // Remove "All"
        .filter((id) => id !== "0")
        .map((id) => id)
    );
  }, [layersById]);

  const defaultValues = useMemo(() => {
    const layers = Object.values(layersById);

    return areas.reduce(
      (acc, area) => {
        acc[area.id] = layers.reduce(
          (acc2, layer) => {
            acc2[layer.id] = layer.areas.includes(area.id);
            return acc2;
          },
          {} as Record<string, boolean>,
        );

        return acc;
      },
      {} as Record<string, Record<string, boolean>>,
    );
  }, [areas, layersById]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const areasByLayer: Record<string, string[]> = {};

    Object.keys(data.dirtyValues).forEach((areaId) => {
      Object.keys(data.dirtyValues[areaId] || {}).forEach((layerId) => {
        areasByLayer[layerId] ||= [...layersById[layerId].areas];

        if (data.dirtyValues[areaId]?.[layerId]) {
          areasByLayer[layerId].push(areaId);
        } else {
          areasByLayer[layerId] = areasByLayer[layerId].filter((id) => id !== areaId);
        }
      });
    });

    const promises = Object.keys(areasByLayer).map((layerId) => {
      return dispatch(
        updateStudyMapLayer({
          studyId: study.id,
          layerId,
          name: layersById[layerId].name,
          areas: areasByLayer[layerId],
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
          onClick={() => setCreateLayerDialogOpen(true)}
          sx={{ mr: 1 }}
        >
          {t("study.modelization.map.layers.add")}
        </Button>
        <Button
          color="primary"
          variant="outlined"
          startIcon={<EditIcon />}
          onClick={() => setUpdateLayerDialogOpen(true)}
        >
          {t("study.modelization.map.layers.edit")}
        </Button>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: "hidden" }}>
        {columns.length > 0 && (
          <TableForm
            key={JSON.stringify(defaultValues)}
            defaultValues={defaultValues}
            tableProps={{
              columns,
              colHeaders: (_, colName) => layersById[colName].name,
              selectionMode: "single",
            }}
            onSubmit={handleSubmit}
          />
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
