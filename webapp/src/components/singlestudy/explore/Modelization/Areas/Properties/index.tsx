import { Box } from "@mui/material";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import usePromise from "../../../../../../hooks/usePromise";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import Form from "../../../../../common/Form";
import PropertiesForm from "./PropertiesForm";
import { getDefaultValues } from "./utils";

function Properties() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const {
    data: defaultValues,
    status,
    isLoading,
    error,
  } = usePromise(() => getDefaultValues(study.id, currentArea));
  console.log("DEFAULT VALUES: ", defaultValues);
  return (
    <Box sx={{ width: "100%", height: "100%" }}>
      <Form
        disableSubmitButton
        formOptions={{ defaultValues }}
        onSubmit={() => console.log("Hey")}
      >
        {PropertiesForm}
      </Form>
    </Box>
  );
}

export default Properties;
