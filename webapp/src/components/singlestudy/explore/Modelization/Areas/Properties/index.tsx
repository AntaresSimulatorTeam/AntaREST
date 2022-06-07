import { Box } from "@mui/material";
import { useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../common/types";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import Form from "../../../../../common/Form";
import { useGetDefaultValues } from "./common";
import PropertiesForm from "./PropertiesForm";
import { defaultPath } from "./utils";

function Properties() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const pathPrefix = useMemo(() => `input/areas/${currentArea}`, [currentArea]);

  const { data: defaultValues } = useGetDefaultValues({
    fieldsInfo: defaultPath,
    studyId: study.id,
    pathPrefix,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

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
