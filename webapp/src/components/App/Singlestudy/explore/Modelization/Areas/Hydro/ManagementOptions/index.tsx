import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../../common/types";
import usePromiseWithSnackbarError from "../../../../../../../../hooks/usePromiseWithSnackbarError";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import Form, { SubmitHandlerPlus } from "../../../../../../../common/Form";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import { Root } from "../style";
import Fields from "./Fields";
import {
  getManagementOptionsFormFields,
  HydroFormFields,
  setManagementOptionsFormFields,
} from "./utils";

function ManagementOptions() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  const res = usePromiseWithSnackbarError(
    () => getManagementOptionsFormFields(studyId, areaId),
    {
      errorMessage: "Cannot get management options fields",
      deps: [studyId, areaId],
    }
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<HydroFormFields>) => {
    setManagementOptionsFormFields(studyId, areaId, data.dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <UsePromiseCond
        response={res}
        ifResolved={(defaultValues) => (
          <Form config={{ defaultValues }} onSubmit={handleSubmit} autoSubmit>
            <Fields />
          </Form>
        )}
      />
    </Root>
  );
}

export default ManagementOptions;
