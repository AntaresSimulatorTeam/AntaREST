/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useState } from "react";
import axios, { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { getStudyData, importFile } from "../../../../services/api/study";
import { MatrixType } from "../../../../common/types";
import { Header, Root, Content } from "./DebugView/StudyDataView/style";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import NoContent from "../../../common/page/NoContent";
import ImportForm from "../../../common/ImportForm";
import SimpleLoader from "../../../common/loaders/SimpleLoader";
import EditableMatrix from "../../../common/EditableMatrix";

const logErr = debug("antares:createimportform:error");

function StudyMatrixView() {
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);
  const url = "/input/load/series/load_ii";
  const study = "5ed36c48-e655-45df-aae0-0ce7c6d0ff8e";

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
      await importFile(file, study, "/input/load/series/load_ii");
    } catch (e) {
      logErr("Failed to import file", file, e);
      enqueueErrorSnackbar(t("studymanager:failtosavedata"), e as AxiosError);
    }
    enqueueSnackbar(t("studymanager:savedatasuccess"), { variant: "success" });
  };

  useEffect(() => {
    loadFileData();
  }, []);

  return (
    <>
      <Root>
        <Header>
          <ImportForm text={t("main:import")} onImport={onImport} />
        </Header>
        <Content>
          {!loaded && <SimpleLoader />}
          {loaded && data && Object.keys(data).length > 0 ? (
            <EditableMatrix matrix={data} readOnly={false} />
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
          <SimpleLoader />
        </div>
      )}
    </>
  );
}

export default StudyMatrixView;
