import { useOutletContext } from "react-router";
import * as R from "ramda";
import { useState } from "react";
import { StudyMetadata } from "../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import Form, { SubmitHandlerPlus } from "../../../../../common/Form";
import Fields from "./Fields";
import ThematicTrimmingDialog from "./dialogs/ThematicTrimmingDialog";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import PlaylistDialog from "./dialogs/PlaylistDialog";
import {
  GeneralFormFields,
  getGeneralFormFields,
  setGeneralFormFields,
} from "./utils";

function GeneralParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [dialog, setDialog] = useState<"thematicTrimming" | "playlist" | "">(
    ""
  );

  const res = usePromiseWithSnackbarError(
    () => getGeneralFormFields(study.id),
    { errorMessage: "Cannot get General form fields", deps: [study.id] } // TODO i18n
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<GeneralFormFields>) => {
    return setGeneralFormFields(study.id, data.dirtyValues);
  };

  const handleCloseDialog = () => {
    setDialog("");
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifResolved={(data) => (
        <Form
          config={{ defaultValues: data }}
          onSubmit={handleSubmit}
          autoSubmit
        >
          <Fields setDialog={setDialog} />
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
            [
              R.equals("playlist"),
              () => (
                <PlaylistDialog
                  open
                  study={study}
                  onClose={handleCloseDialog}
                />
              ),
            ],
          ])(dialog)}
        </Form>
      )}
    />
  );
}

export default GeneralParameters;
