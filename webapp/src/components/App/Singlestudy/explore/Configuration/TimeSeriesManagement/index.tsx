import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import Form, { SubmitHandlerPlus } from "../../../../../common/Form";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import Fields from "./Fields";
import {
  getTimeSeriesFormFields,
  setTimeSeriesFormFields,
  TSFormFields,
} from "./utils";

function TimeSeriesManagement() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const res = usePromiseWithSnackbarError(
    () => getTimeSeriesFormFields(study.id),
    // TODO i18n
    { errorMessage: "Cannot get time series fields", deps: [study.id] }
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<TSFormFields>) => {
    return setTimeSeriesFormFields(study.id, data.dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifPending={() => <SimpleLoader />}
      ifRejected={(error) => <div>{error?.toString()}</div>}
      ifResolved={(defaultValues) => (
        <Form config={{ defaultValues }} onSubmit={handleSubmit} autoSubmit>
          <Fields />
        </Form>
      )}
    />
  );
}

export default TimeSeriesManagement;
