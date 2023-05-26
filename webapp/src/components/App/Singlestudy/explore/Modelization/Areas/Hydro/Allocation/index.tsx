import { Grid } from "@mui/material";
import { useOutletContext } from "react-router";
import { useState } from "react";
import Form from "../../../../../../../common/Form";
import Fields from "./Fields";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import {
  AllocationFormFields,
  getAllocationFormFields,
  setAllocationFormFields,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import HydroMatrixDialog from "../HydroMatrixDialog";
import { HydroMatrixType } from "../utils";
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
          backgroundImage:
            "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
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
          type={HydroMatrixType.Allocation}
          open={matrixDialogOpen}
          onClose={() => setMatrixDialogOpen(false)}
        />
      )}
    </FormBox>
  );
}

export default Allocation;
