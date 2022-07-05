import { useOutletContext } from "react-router";
import * as R from "ramda";
import { useState } from "react";
import { StudyMetadata } from "../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import { getFormValues } from "./utils";
import { PromiseStatus } from "../../../../../../hooks/usePromise";
import Form from "../../../../../common/Form";
import Fields from "./Fields";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import ThematicTrimmingDialog from "./dialogs/ThematicTrimmingDialog";

function GeneralParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [dialog, setDialog] = useState<"thematicTrimming" | "">("");

  const { data, status, error } = usePromiseWithSnackbarError(
    () => getFormValues(study.id),
    { errorMessage: "Cannot get study data", deps: [study.id] } // TODO i18n
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCloseDialog = () => {
    setDialog("");
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return R.cond([
    [
      R.either(R.equals(PromiseStatus.Idle), R.equals(PromiseStatus.Pending)),
      () => <SimpleLoader />,
    ],
    [R.equals(PromiseStatus.Rejected), () => <div>{error}</div>],
    [
      R.equals(PromiseStatus.Resolved),
      () => (
        <Form autoSubmit config={{ defaultValues: data }}>
          <Fields study={study} setDialog={setDialog} />
          {R.cond([
            [
              R.equals("thematicTrimming"),
              () => (
                <ThematicTrimmingDialog
                  open
                  study={study}
                  onClose={handleCloseDialog}
                />
              ),
            ],
          ])(dialog)}
        </Form>
      ),
    ],
  ])(status);
}

export default GeneralParameters;
