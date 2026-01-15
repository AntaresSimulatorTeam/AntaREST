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
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { Grid } from "@mui/material";
import { useState } from "react";
import useAppSelector from "../../../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../../../redux/selectors";
import HydroMatrixDialog from "../HydroMatrixDialog";
import { FormBox, FormPaper } from "../style";
import { HydroMatrix } from "../utils";
import ViewMatrixButton from "../ViewMatrixButton";
import Fields from "./-components/Fields";
import {
  type AllocationFormFields,
  getAllocationFormFields,
  setAllocationFormFields,
} from "./-utils";

function Allocation() {
  const study = useStudy();
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);
  const areaId = useAppSelector(getCurrentAreaId);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<AllocationFormFields>) => {
    return setAllocationFormFields(study.id, areaId, {
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
                defaultValues: () => getAllocationFormFields(study.id, areaId),
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
          type={HydroMatrix.Allocation}
          open={matrixDialogOpen}
          onClose={() => setMatrixDialogOpen(false)}
        />
      )}
    </FormBox>
  );
}

export default Allocation;
