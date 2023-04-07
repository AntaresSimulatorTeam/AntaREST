import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import Form from "../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  AdequacyPatchFormFields,
  getAdequacyPatchFormFields,
  setAdequacyPatchFormFields,
} from "./utils";

function AdequacyPatch() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<AdequacyPatchFormFields>
  ) => {
    return setAdequacyPatchFormFields(study.id, data.dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id}
      config={{
        defaultValues: () => getAdequacyPatchFormFields(study.id),
      }}
      onSubmit={handleSubmit}
      autoSubmit
    >
      <Fields />
    </Form>
  );
}

export default AdequacyPatch;
