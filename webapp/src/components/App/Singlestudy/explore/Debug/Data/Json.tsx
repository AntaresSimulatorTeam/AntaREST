import { useState } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import SaveIcon from "@mui/icons-material/Save";
import { Box, Button, Typography } from "@mui/material";
import { useUpdateEffect } from "react-use";
import { editStudy, getStudyData } from "../../../../../../services/api/study";
import { Header, Root } from "./style";
import JSONEditor from "../../../../../common/JSONEditor";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";

interface Props {
  path: string;
  studyId: string;
}

function Json({ path, studyId }: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [jsonData, setJsonData] = useState<string | null>(null);
  const [isSaveAllowed, setSaveAllowed] = useState(false);

  const res = usePromiseWithSnackbarError(
    () => getStudyData(studyId, path, -1),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, path],
    },
  );

  // Reset save button when path changes
  useUpdateEffect(() => {
    setSaveAllowed(false);
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
        setSaveAllowed(false);
      } catch (e) {
        enqueueErrorSnackbar(t("studies.error.saveData"), e as AxiosError);
      }
    }
  };

  const handleJsonChange = (newJson: string) => {
    setJsonData(newJson);
    setSaveAllowed(true);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <Header>
        <Button
          variant="outlined"
          color="primary"
          startIcon={<SaveIcon sx={{ width: 15, height: 15 }} />}
          onClick={handleSaveJson}
          disabled={!isSaveAllowed}
        >
          <Typography sx={{ fontSize: "12px" }}>{t("global.save")}</Typography>
        </Button>
      </Header>
      <UsePromiseCond
        response={res}
        ifResolved={(json) => (
          <Box
            sx={{
              width: 1,
              height: 1,
            }}
          >
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
    </Root>
  );
}

export default Json;
