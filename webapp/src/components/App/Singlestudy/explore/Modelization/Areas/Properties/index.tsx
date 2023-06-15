import { Paper } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import Form from "../../../../../../common/Form";
import {
  PropertiesFormFields,
  getPropertiesFormFields,
  setPropertiesFormFields,
} from "./utils";
import Fields from "./Fields";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";

function Properties() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentAreaId = useAppSelector(getCurrentAreaId);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<PropertiesFormFields>) => {
    const { dirtyValues } = data;
    return setPropertiesFormFields(study.id, currentAreaId, dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Paper sx={{ width: 1, height: 1, padding: 2, overflow: "auto" }}>
      <Form
        key={study.id + currentAreaId}
        config={{
          defaultValues: () => getPropertiesFormFields(study.id, currentAreaId),
        }}
        onSubmit={handleSubmit}
      >
        <Fields />
      </Form>
    </Paper>
  );
}

export default Properties;
