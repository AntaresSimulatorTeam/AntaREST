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

  const handleSubmit = async (
    data: SubmitHandlerPlus<AdvancedParamsFormFields>
  ) => {
    const values = { ...data.dirtyValues };

    // Get a comma separated string from accuracyOnCorrelation array as expected by the api
    if (values.accuracyOnCorrelation) {
      values.accuracyOnCorrelation = (
        values.accuracyOnCorrelation as unknown as string[]
      ).join(", ");
    }

    return setAdvancedParamsFormFields(study.id, values).then(() => {
      if (values.renewableGenerationModelling) {
        dispatch(
          updateStudySynthesis({
            id: study.id,
            changes: { enr_modelling: values.renewableGenerationModelling },
          })
        );
      }
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id}
      config={{
        asyncDefaultValues: () => getAdvancedParamsFormFields(study.id),
      }}
      onSubmit={handleSubmit}
      autoSubmit
    >
      <Fields version={Number(study.version)} />
    </Form>
  );
}

export default AdvancedParameters;
