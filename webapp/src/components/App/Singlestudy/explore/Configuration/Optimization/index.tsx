import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import Form, { SubmitHandlerPlus } from "../../../../../common/Form";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import Fields from "./Fields";
import {
  getOptimizationFormFields,
  OptimizationFormFields,
  setOptimizationFormFields,
} from "./utils";

function Optimization() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const res = usePromiseWithSnackbarError(
    () => getOptimizationFormFields(study.id),
    // TODO i18n
    { errorMessage: "Cannot get optimization fields", deps: [study.id] }
  );

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
    <UsePromiseCond
      response={res}
      ifResolved={(defaultValues) => (
        <Form config={{ defaultValues }} onSubmit={handleSubmit} autoSubmit>
          <Fields study={study} />
        </Form>
      )}
    />
  );
}

export default Optimization;
