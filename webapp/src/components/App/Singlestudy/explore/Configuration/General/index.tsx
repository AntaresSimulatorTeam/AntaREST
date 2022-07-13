import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import { getFormValues } from "./utils";
import Form from "../../../../../common/Form";
import Fields from "./Fields";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";

function GeneralParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const { data, status, error } = usePromiseWithSnackbarError(
    () => getFormValues(study.id),
    { errorMessage: "Cannot get study data", deps: [study.id] } // TODO i18n
  );

  return (
    <UsePromiseCond
      status={status}
      ifPending={<SimpleLoader />}
      ifRejected={<div>{error}</div>}
      ifResolved={
        <Form autoSubmit config={{ defaultValues: data }}>
          <Fields study={study} />
        </Form>
      }
    />
  );
}

export default GeneralParameters;
