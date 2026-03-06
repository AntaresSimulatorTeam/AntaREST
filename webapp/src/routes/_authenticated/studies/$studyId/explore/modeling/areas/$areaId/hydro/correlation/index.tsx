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
import { GridLegacy as Grid } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import HydroMatrixDialog from "../-components/HydroMatrixDialog";
import { FormBox, FormPaper } from "../-components/style";
import ViewMatrixButton from "../-components/ViewMatrixButton";
import { HydroMatrixType } from "../-utils";
import Fields from "./-components/Fields";
import {
  getCorrelationFormFields,
  setCorrelationFormFields,
  type CorrelationFormFields,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/correlation/",
)({
  component: Correlation,
});

function Correlation() {
  const { studyId, areaId } = Route.useParams();
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<CorrelationFormFields>) => {
    return setCorrelationFormFields(studyId, areaId, {
      correlation: data.values.correlation,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormBox>
      <FormPaper>
        <Grid container justifyContent="flex-end" alignItems="flex-start">
          <Grid item xs>
            <Form
              key={areaId}
              config={{
                defaultValues: () => getCorrelationFormFields(studyId, areaId),
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
              label="study.modeling.hydro.correlation.viewMatrix"
              onClick={() => setMatrixDialogOpen(true)}
            />
          </Grid>
        </Grid>
      </FormPaper>
      {matrixDialogOpen && (
        <HydroMatrixDialog
          type={HydroMatrixType.Correlation}
          open={matrixDialogOpen}
          onClose={() => setMatrixDialogOpen(false)}
        />
      )}
    </FormBox>
  );
}
