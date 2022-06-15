import { useOutletContext } from "react-router";
import * as R from "ramda";
import { StudyMetadata } from "../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import { getFormValues } from "./utils";
import { PromiseStatus } from "../../../../../hooks/usePromise";
import Form from "../../../../common/Form";
import Fields from "./Fields";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";

function GeneralParameters() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const { data, status, error } = usePromiseWithSnackbarError(
    () => getFormValues(study.id),
    { errorMessage: "Cannot get study data" }, // TODO i18n
    [study.id]
  );

  return R.cond([
    [
      R.either(R.equals(PromiseStatus.Idle), R.equals(PromiseStatus.Pending)),
      () => <SimpleLoader />,
    ],
    [R.equals(PromiseStatus.Rejected), () => <div>{error}</div>],
    [
      R.equals(PromiseStatus.Resolved),
      () => (
        <Form autoSubmit config={{ defaultValues: data }}>
          <Fields study={study} />
        </Form>
      ),
    ],
  ])(status);
}

export default GeneralParameters;
