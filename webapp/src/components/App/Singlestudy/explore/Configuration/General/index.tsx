import { useOutletContext } from "react-router";
import * as R from "ramda";
import { useState } from "react";
import { StudyMetadata } from "../../../../../../common/types";
import Form from "../../../../../common/Form";
import Fields from "./Fields";
import ThematicTrimmingDialog from "./dialogs/ThematicTrimmingDialog";
import PlaylistDialog from "./dialogs/PlaylistDialog";
import {
  GeneralFormFields,
  getGeneralFormFields,
  setGeneralFormFields,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";

function GeneralParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [dialog, setDialog] = useState<"thematicTrimming" | "playlist" | "">(
    ""
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
    <>
      <Form
        key={study.id}
        config={{ asyncDefaultValues: () => getGeneralFormFields(study.id) }}
        onSubmit={handleSubmit}
        autoSubmit
      >
        <Fields setDialog={setDialog} />
      </Form>
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
            <PlaylistDialog open study={study} onClose={handleCloseDialog} />
          ),
        ],
      ])(dialog)}
    </>
  );
}

export default GeneralParameters;
