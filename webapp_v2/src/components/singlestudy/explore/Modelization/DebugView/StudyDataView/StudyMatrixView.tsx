/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useState } from "react";
import axios, { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { getStudyData, importFile } from "../../../../../../services/api/study";
import { MatrixType } from "../../../../../../common/types";
import { Header, Root, Content } from "./style";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import MainContentLoader from "../../../../../common/loaders/MainContentLoader";
import NoContent from "../../../../../common/page/NoContent";
import ImportForm from "../../../../../common/ImportForm";
import SimpleLoader from "../../../../../common/loaders/SimpleLoader";
import MatrixView from "../../../../../common/MatrixView";

const logErr = debug("antares:createimportform:error");

interface PropTypes {
  study: string;
  url: string;
  refreshView: () => void;
  filterOut: Array<string>;
}

function StudyMatrixView(props: PropTypes) {
  const { study, url, filterOut, refreshView } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);
  const [isEditable, setEditable] = useState<boolean>(true);
  const [formatedPath, setFormatedPath] = useState<string>("");

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      if (typeof res === "string") {
        const fixed = res.replace(/NaN/g, '"NaN"');
        setData(JSON.parse(fixed));
      } else {
        setData(res);
      }
    } catch (e) {
      if (axios.isAxiosError(e)) {
        enqueueErrorSnackbar(
          t("studymanager:failtoretrievedata"),
          e as AxiosError
        );
      } else {
        enqueueSnackbar(t("studymanager:failtoretrievedata"), {
          variant: "error",
        });
      }
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
      <Root>
        {isEditable && (
          <Header>
            <ImportForm text={t("main:import")} onImport={onImport} />
          </Header>
        )}
        <Content>
          {!loaded && <SimpleLoader />}
          {loaded && data && Object.keys(data).length > 0 ? (
            <MatrixView matrix={data} readOnly />
          ) : (
            loaded && (
              <NoContent
                title="data:matrixEmpty"
                callToAction={
                  <ImportForm text={t("main:import")} onImport={onImport} />
                }
              />
            )
          )}
        </Content>
      </Root>
      {!loaded && (
        <div style={{ width: "100%", height: "100%", position: "relative" }}>
          <MainContentLoader />
        </div>
      )}
    </>
  );
}

export default StudyMatrixView;
