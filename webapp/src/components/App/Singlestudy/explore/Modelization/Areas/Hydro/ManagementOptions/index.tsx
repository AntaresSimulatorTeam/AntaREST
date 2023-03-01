import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import DocLink from "../../../../../../../common/DocLink";
import Form from "../../../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { ACTIVE_WINDOWS_DOC_PATH } from "../../../BindingConstraints/BindingConstView/utils";
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
    <>
      <DocLink to={`${ACTIVE_WINDOWS_DOC_PATH}#hydro`} isAbsolute />
      <Form
        key={studyId + areaId}
        config={{
          asyncDefaultValues: () =>
            getManagementOptionsFormFields(studyId, areaId),
        }}
        onSubmit={handleSubmit}
        autoSubmit
      >
        <Fields />
      </Form>
    </>
  );
}

export default ManagementOptions;
