import { useState } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import SaveIcon from "@mui/icons-material/Save";
import { Box, Button } from "@mui/material";
import { useUpdateEffect } from "react-use";
import { editStudy, getStudyData } from "../../../../../../services/api/study";
import JSONEditor from "../../../../../common/JSONEditor";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import ViewWrapper from "../../../../../common/page/ViewWrapper";

interface Props {
  path: string;
  studyId: string;
}

function Json({ path, studyId }: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [jsonData, setJsonData] = useState<string | null>(null);
  const [isSaveAllowed, setIsSaveAllowed] = useState(false);

  const res = usePromiseWithSnackbarError(
    () => getStudyData(studyId, path, -1),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, path],
    },
  );

  // Reset save button when path changes
  useUpdateEffect(() => {
    setIsSaveAllowed(false);
  }, [studyId, path]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSaveJson = async () => {
    if (isSaveAllowed && jsonData) {
      try {
        await editStudy(jsonData, studyId, path);
        enqueueSnackbar(t("studies.success.saveData"), {
          variant: "success",
        });
        setIsSaveAllowed(false);
      } catch (e) {
        enqueueErrorSnackbar(t("studies.error.saveData"), e as AxiosError);
      }
    }
  };

  const handleJsonChange = (newJson: string) => {
    setJsonData(newJson);
    setIsSaveAllowed(true);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <Box>
        <Button
          variant="contained"
          size="small"
          startIcon={<SaveIcon />}
          onClick={handleSaveJson}
          disabled={!isSaveAllowed}
        >
          {t("global.save")}
        </Button>
      </Box>
      <UsePromiseCond
        response={res}
        ifResolved={(json) => (
          <Box sx={{ overflow: "auto" }}>
            <JSONEditor
              json={json}
              onChangeText={handleJsonChange}
              modes={["tree", "code"]}
              enableSort={false}
              enableTransform={false}
            />
          </Box>
        )}
      />
    </ViewWrapper>
  );
}

export default Json;
