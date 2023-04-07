import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import Form from "../../../../../../common/Form";
import PropertiesForm from "./PropertiesForm";
import { getDefaultValues } from "./utils";

function Properties() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const [t] = useTranslation();

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      <Form
        key={study.id + currentArea}
        config={{
          defaultValues: () => getDefaultValues(study.id, currentArea, t),
        }}
        autoSubmit
      >
        {(formApi) => (
          <PropertiesForm
            {...formApi}
            areaName={currentArea}
            studyId={study.id}
            studyVersion={Number(study.version)}
          />
        )}
      </Form>
    </Box>
  );
}

export default Properties;
