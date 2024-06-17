import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import { updateStudySynthesis } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import Form from "../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  AdvancedParamsFormFields,
  getAdvancedParamsFormFields,
  setAdvancedParamsFormFields,
} from "./utils";

function AdvancedParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({
    dirtyValues,
  }: SubmitHandlerPlus<AdvancedParamsFormFields>) => {
    return setAdvancedParamsFormFields(study.id, dirtyValues);
  };

  const handleSubmitSuccessful = ({
    dirtyValues: { renewableGenerationModelling },
  }: SubmitHandlerPlus<AdvancedParamsFormFields>) => {
    if (renewableGenerationModelling) {
      dispatch(
        updateStudySynthesis({
          id: study.id,
          changes: { enr_modelling: renewableGenerationModelling },
        }),
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id}
      config={{
        defaultValues: () => getAdvancedParamsFormFields(study.id),
      }}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      enableUndoRedo
    >
      <Fields version={Number(study.version)} />
    </Form>
  );
}

export default AdvancedParameters;
