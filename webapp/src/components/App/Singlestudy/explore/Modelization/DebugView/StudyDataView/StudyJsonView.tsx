/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect } from "react";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import SaveIcon from "@mui/icons-material/Save";
import { Box, Button, Typography } from "@mui/material";
import {
  editStudy,
  getStudyData,
} from "../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import { Header, Root } from "./style";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import JSONEditor from "../../../../../../common/JSONEditor";

interface PropTypes {
  data: string;
  study: string;
  filterOut: Array<string>;
}

function StudyJsonView(props: PropTypes) {
  const { data, study, filterOut } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [jsonData, setJsonData] = useState<object>();
  const [loaded, setLoaded] = useState(false);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);
  const [isEditable, setEditable] = useState<boolean>(true);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleJsonChange = (newJsonData: any) => {
    setJsonData(newJsonData);
    setSaveAllowed(true);
  };

  const saveData = async () => {
    const tmpDataPath = data.split("/").filter((item) => item);
    const tmpPath = tmpDataPath.join("/");
    if (loaded && jsonData) {
      try {
        await editStudy(jsonData, study, tmpPath);
        enqueueSnackbar(t("studies.success.saveData"), {
          variant: "success",
        });
        setSaveAllowed(false);
      } catch (e) {
        enqueueErrorSnackbar(t("studies.error.saveData"), e as AxiosError);
      }
    } else {
      enqueueSnackbar(t("studies.error.saveData"), { variant: "error" });
    }
  };

  useEffect(() => {
    (async () => {
      setJsonData(undefined);
      setLoaded(false);
      const tmpDataPath = data.split("/").filter((item) => item);
      if (tmpDataPath.length > 0) {
        setEditable(!filterOut.includes(tmpDataPath[0]));
      }
      try {
        const res = await getStudyData(study, data, -1);
        setJsonData(res);
        setSaveAllowed(false);
      } catch (e) {
        enqueueErrorSnackbar(t("studies.error.retrieveData"), e as AxiosError);
      } finally {
        setLoaded(true);
      }
    })();
  }, [data, filterOut]);

  return (
    <Root>
      {isEditable && (
        <Header>
          <Button
            variant="outlined"
            color="primary"
            sx={{ border: "2px solid" }}
            startIcon={
              <SaveIcon sx={{ m: 0.2, width: "16px", height: "16px" }} />
            }
            onClick={() => saveData()}
            disabled={!saveAllowed}
          >
            <Typography sx={{ fontSize: "12px", m: 0.2 }}>
              {t("global.save")}
            </Typography>
          </Button>
        </Header>
      )}
      {jsonData && (
        <Box
          sx={{
            width: 1,
            height: 1,
            overflow: "auto",
            position: "relative",
          }}
        >
          <JSONEditor
            json={jsonData}
            onChangeJSON={handleJsonChange}
            onChangeText={(json) => console.log(json)}
            modes={["tree", "code"]}
            enableSort={false}
            enableTransform={false}
          />
        </Box>
      )}
      {!loaded && (
        <Box width="100%" height="100%" position="relative">
          <SimpleLoader />
        </Box>
      )}
    </Root>
  );
}

export default StudyJsonView;
