import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import usePromise from "../../../../../../../hooks/usePromise";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import Form from "../../../../../../common/Form";
import PropertiesForm from "./PropertiesForm";
import { getDefaultValues } from "./utils";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

function Properties() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const [t] = useTranslation();
  const res = usePromise(
    () => getDefaultValues(study.id, currentArea, t),
    [study.id, currentArea]
  );

  return (
    <Box sx={{ width: "100%", height: "100%", overflowY: "auto" }}>
      <UsePromiseCond
        response={res}
        ifResolved={(data) => (
          <Form autoSubmit config={{ defaultValues: data }}>
            {(formObj) =>
              PropertiesForm({
                ...formObj,
                areaName: currentArea,
                studyId: study.id,
                studyVersion: Number(study.version),
              })
            }
          </Form>
        )}
      />
    </Box>
  );
}

export default Properties;
