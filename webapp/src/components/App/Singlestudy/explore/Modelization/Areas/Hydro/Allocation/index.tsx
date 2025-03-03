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

import { Grid } from "@mui/material";
import { useOutletContext } from "react-router";
import { useState } from "react";
import Form from "../../../../../../../common/Form";
import Fields from "./Fields";
import type { StudyMetadata } from "../../../../../../../../types/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import {
  getAllocationFormFields,
  setAllocationFormFields,
  type AllocationFormFields,
} from "./utils";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import HydroMatrixDialog from "../HydroMatrixDialog";
import { HydroMatrix } from "../utils";
import { FormBox, FormPaper } from "../style";
import ViewMatrixButton from "../ViewMatrixButton";

function Allocation() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);
  const areaId = useAppSelector(getCurrentAreaId);

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
              key={studyId + areaId}
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
              label="study.modelization.hydro.allocation.viewMatrix"
              onClick={() => setMatrixDialogOpen(true)}
            />
          </Grid>
        </Grid>
      </FormPaper>
      {matrixDialogOpen && (
        <HydroMatrixDialog
          type={HydroMatrix.Allocation}
          open={matrixDialogOpen}
          onClose={() => setMatrixDialogOpen(false)}
        />
      )}
    </FormBox>
  );
}

export default Allocation;
