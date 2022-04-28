/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useState } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { getStudyData, importFile } from "../../../../../../services/api/study";
import { Header, Root, Content } from "./style";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import MainContentLoader from "../../../../../common/loaders/MainContentLoader";
import ImportForm from "../../../../../common/ImportForm";

const logErr = debug("antares:createimportform:error");

interface PropTypes {
  study: string;
  url: string;
  refreshView: () => void;
  filterOut: Array<string>;
}

function StudyDataView(props: PropTypes) {
  const { study, url, filterOut, refreshView } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<string>();
  const [loaded, setLoaded] = useState(false);
  const [isEditable, setEditable] = useState<boolean>(true);
  const [formatedPath, setFormatedPath] = useState<string>("");

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      setData(res);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studymanager:failtoretrievedata"),
        e as AxiosError
      );
    } finally {
      setLoaded(true);
    }
  };

  const onImport = async (file: File) => {
    try {
      await importFile(file, study, formatedPath);
    } catch (e) {
      logErr("Failed to import file", file, e);
      enqueueErrorSnackbar(t("studymanager:failtosavedata"), e as AxiosError);
    }
    refreshView();
    enqueueSnackbar(t("studymanager:savedatasuccess"), { variant: "success" });
  };

  useEffect(() => {
    const urlParts = url.split("/");
    const tmpUrl = urlParts.filter((item) => item);
    setFormatedPath(tmpUrl.join("/"));
    if (tmpUrl.length > 0) {
      setEditable(!filterOut.includes(tmpUrl[0]));
    }
    if (urlParts.length < 2) {
      enqueueSnackbar(t("studymanager:failtoretrievedata"), {
        variant: "error",
      });
      return;
    }
    loadFileData();
  }, [url, filterOut]);

  return (
    <>
      {data && (
        <Root>
          {isEditable && (
            <Header>
              <ImportForm text={t("main:import")} onImport={onImport} />
            </Header>
          )}
          <Content>
            <code style={{ whiteSpace: "pre" }}>{data}</code>
          </Content>
        </Root>
      )}
      {!loaded && (
        <Box width="100%" height="100%" position="relative">
          <MainContentLoader />
        </Box>
      )}
    </>
  );
}

export default StudyDataView;
