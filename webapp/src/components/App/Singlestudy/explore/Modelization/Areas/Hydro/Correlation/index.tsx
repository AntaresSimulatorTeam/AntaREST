/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useState } from "react";
import { useOutletContext } from "react-router";

import { Grid } from "@mui/material";

import { StudyMetadata } from "@/common/types";
import Form from "@/components/common/Form";
import { SubmitHandlerPlus } from "@/components/common/Form/types";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getCurrentAreaId } from "@/redux/selectors";

import HydroMatrixDialog from "../HydroMatrixDialog";
import { FormBox, FormPaper } from "../style";
import { HydroMatrix } from "../utils";
import ViewMatrixButton from "../ViewMatrixButton";

import Fields from "./Fields";
import {
  CorrelationFormFields,
  getCorrelationFormFields,
  setCorrelationFormFields,
} from "./utils";

function Correlation() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);
  const areaId = useAppSelector(getCurrentAreaId);

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
              key={studyId + areaId}
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
              label="study.modelization.hydro.correlation.viewMatrix"
              onClick={() => setMatrixDialogOpen(true)}
            />
          </Grid>
        </Grid>
      </FormPaper>
      {matrixDialogOpen && (
        <HydroMatrixDialog
          type={HydroMatrix.Correlation}
          open={matrixDialogOpen}
          onClose={() => setMatrixDialogOpen(false)}
        />
      )}
    </FormBox>
  );
}

export default Correlation;
