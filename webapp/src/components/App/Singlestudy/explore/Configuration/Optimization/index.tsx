import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import Form from "../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  getOptimizationFormFields,
  OptimizationFormFields,
  setOptimizationFormFields,
} from "./utils";

function Optimization() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<OptimizationFormFields>
  ) => {
    return setOptimizationFormFields(study.id, data.dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id}
      config={{ defaultValues: () => getOptimizationFormFields(study.id) }}
      onSubmit={handleSubmit}
      autoSubmit
    >
      <Fields study={study} />
    </Form>
  );
}

export default Optimization;
