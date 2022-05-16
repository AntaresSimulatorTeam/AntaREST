/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect } from "react";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import ReactJson from "react-json-view";
import SaveIcon from "@mui/icons-material/Save";
import { Box, Button, Typography } from "@mui/material";
import { editStudy, getStudyData } from "../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { Header, Root, Content } from "./style";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";

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

  const saveData = async () => {
    const tmpDataPath = data.split("/").filter((item) => item);
    const tmpPath = tmpDataPath.join("/");
    if (loaded && jsonData) {
      try {
        await editStudy(jsonData, study, tmpPath);
        enqueueSnackbar(t("studymanager:savedatasuccess"), {
          variant: "success",
        });
        setSaveAllowed(false);
      } catch (e) {
        enqueueErrorSnackbar(t("studymanager:failtosavedata"), e as AxiosError);
      }
    } else {
      enqueueSnackbar(t("studymanager:failtosavedata"), { variant: "error" });
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
        enqueueErrorSnackbar(
          t("studymanager:failtoretrievedata"),
          e as AxiosError
        );
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
              {t("global:global.save")}
            </Typography>
          </Button>
        </Header>
      )}
      <Content>
        {jsonData && (
          <ReactJson
            src={jsonData}
            onEdit={
              isEditable
                ? (e) => {
                    setJsonData(e.updated_src);
                    setSaveAllowed(true);
                  }
                : undefined
            }
            theme="monokai"
          />
        )}
        {!loaded && (
          <Box width="100%" height="100%" position="relative">
            <SimpleLoader />
          </Box>
        )}
      </Content>
    </Root>
  );
}

export default StudyJsonView;
