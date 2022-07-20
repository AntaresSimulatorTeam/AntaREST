import { useOutletContext } from "react-router";
import * as R from "ramda";
import { useState } from "react";
import { StudyMetadata } from "../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import { getFormValues } from "./utils";
import Form from "../../../../../common/Form";
import Fields from "./Fields";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import ThematicTrimmingDialog from "./dialogs/ThematicTrimmingDialog";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";

function GeneralParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [dialog, setDialog] = useState<"thematicTrimming" | "">("");

  const res = usePromiseWithSnackbarError(
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

  const renderDialog = R.cond([
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
  ]);

  return (
    <UsePromiseCond
      response={res}
      ifPending={() => <SimpleLoader />}
      ifRejected={(error) => <div>{error}</div>}
      ifResolved={(data) => (
        <Form autoSubmit config={{ defaultValues: data }}>
          <Fields study={study} setDialog={setDialog} />
          {renderDialog(dialog)}
        </Form>
      )}
    />
  );
}

export default GeneralParameters;
