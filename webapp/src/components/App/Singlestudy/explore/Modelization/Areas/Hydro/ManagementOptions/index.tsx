import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import Form from "../../../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
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
    <Form
      key={studyId + areaId}
      config={{
        defaultValues: () => getManagementOptionsFormFields(studyId, areaId),
      }}
      onSubmit={handleSubmit}
      autoSubmit
    >
      <Fields />
    </Form>
  );
}

export default ManagementOptions;
