import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import Form from "../../../../../common/Form";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import Fields from "./Fields";
import { getFormValues } from "./utils";

function TimeSeriesManagement() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const res = usePromiseWithSnackbarError(
    () => getFormValues(study.id),
    { errorMessage: "Cannot get study data", deps: [study.id] } // TODO i18n
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifPending={() => <SimpleLoader />}
      ifRejected={(error) => <div>{error?.toString()}</div>}
      ifResolved={(data) => (
        <Form autoSubmit config={{ defaultValues: data }}>
          <Fields study={study} />
        </Form>
      )}
    />
  );
}

export default TimeSeriesManagement;
