import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import Form from "../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";
import Fields from "./Fields";
import {
  getTimeSeriesFormFields,
  setTimeSeriesFormFields,
  TSFormFields,
} from "./utils";

function TimeSeriesManagement() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

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
    <Form
      key={study.id}
      config={{ defaultValues: () => getTimeSeriesFormFields(study.id) }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      <Fields />
    </Form>
  );
}

export default TimeSeriesManagement;
