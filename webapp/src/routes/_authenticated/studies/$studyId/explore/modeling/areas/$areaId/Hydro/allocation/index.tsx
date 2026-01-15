/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { Grid } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import HydroMatrixDialog from "../HydroMatrixDialog";
import { FormBox, FormPaper } from "../style";
import { HydroMatrixType } from "../utils";
import ViewMatrixButton from "../ViewMatrixButton";
import Fields from "./-components/Fields";
import {
  type AllocationFormFields,
  getAllocationFormFields,
  setAllocationFormFields,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/allocation/",
)({
  component: Allocation,
});

function Allocation() {
  const { studyId, areaId } = Route.useParams();
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<AllocationFormFields>) => {
    return setAllocationFormFields(studyId, areaId, {
      allocation: data.values.allocation,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormBox>
      <FormPaper
        sx={{
          backgroundImage: "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
        }}
      >
        <Grid container justifyContent="flex-end" alignItems="flex-start">
          <Grid item xs>
            <Form
              key={areaId}
              config={{
                defaultValues: () => getAllocationFormFields(studyId, areaId),
              }}
              onSubmit={handleSubmit}
              sx={{ p: 3 }}
              enableUndoRedo
            >
              <Fields />
            </Form>
          </Grid>
          <Grid item>
            <ViewMatrixButton
              label="study.modeling.hydro.allocation.viewMatrix"
              onClick={() => setMatrixDialogOpen(true)}
            />
          </Grid>
        </Grid>
      </FormPaper>
      {matrixDialogOpen && (
        <HydroMatrixDialog
          type={HydroMatrixType.Allocation}
          open={matrixDialogOpen}
          onClose={() => setMatrixDialogOpen(false)}
        />
      )}
    </FormBox>
  );
}
