import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { Box } from "@mui/material";
import { editStudy, getStudyData } from "../../../../../../services/api/study";
import JSONEditor, { JSONEditorProps } from "../../../../../common/JSONEditor";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import ViewWrapper from "../../../../../common/page/ViewWrapper";
import type { DataCompProps } from "../utils";

function Json({ filePath, studyId }: DataCompProps) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  const res = usePromiseWithSnackbarError(
    () => getStudyData(studyId, filePath, -1),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, filePath],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSave: JSONEditorProps["onSave"] = (json) => {
    return editStudy(json, studyId, filePath);
  };

  const handleSaveSuccessful = () => {
    enqueueSnackbar(t("studies.success.saveData"), {
      variant: "success",
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <UsePromiseCond
        response={res}
        ifResolved={(json) => (
          <Box sx={{ overflow: "auto" }}>
            <JSONEditor
              json={json}
              modes={["tree", "code"]}
              enableSort={false}
              enableTransform={false}
              onSave={handleSave}
              onSaveSuccessful={handleSaveSuccessful}
            />
          </Box>
        )}
      />
    </ViewWrapper>
  );
}

export default Json;
