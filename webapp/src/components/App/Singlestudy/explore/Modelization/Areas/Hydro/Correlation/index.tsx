import { Grid } from "@mui/material";
import { useOutletContext } from "react-router";
import { useState } from "react";
import Form from "../../../../../../../common/Form";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import {
  CorrelationFormFields,
  getCorrelationFormFields,
  setCorrelationFormFields,
} from "./utils";
import Fields from "./Fields";
import HydroMatrixDialog from "../HydroMatrixDialog";
import { HydroMatrixType } from "../utils";
import { FormBox, FormPaper } from "../style";
import ViewMatrixButton from "../ViewMatrixButton";

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
            >
              <Fields />
            </Form>
          </Grid>
          <Grid item>
            <ViewMatrixButton
              label="study.modelization.hydro.correlation.view"
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

export default Correlation;
