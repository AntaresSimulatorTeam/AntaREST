import { useEffect, useState } from "react";
import axios, { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { Box, Typography, Divider, ButtonGroup, Button } from "@mui/material";
import TableViewIcon from "@mui/icons-material/TableView";
import BarChartIcon from "@mui/icons-material/BarChart";
import GetAppOutlinedIcon from "@mui/icons-material/GetAppOutlined";
import { getStudyData, importFile } from "../../../../../services/api/study";
import { MatrixType } from "../../../../../common/types";
import { Header, Root, Content } from "../DebugView/StudyDataView/style";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import NoContent from "../../../../common/page/NoContent";
import ImportDialog from "../../../../common/dialogs/ImportDialog";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";
import EditableMatrix from "../../../../common/EditableMatrix";
import { StyledButton } from "./style";
import { editMatrix } from "../../../../../services/api/matrix";
import { slice } from "./utils";
import { CellChange } from "./type";

const logErr = debug("antares:createimportform:error");

function StudyMatrixView() {
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);
  const [toggleView, setToggleView] = useState(true);
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const url = "input/load/series/load_ii";
  const study = "5ed36c48-e655-45df-aae0-0ce7c6d0ff8e";

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, "/input/load/series/load_ii");
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
      await importFile(file, study, url);
    } catch (e) {
      logErr("Failed to import file", file, e);
      enqueueErrorSnackbar(t("studymanager:failtosavedata"), e as AxiosError);
    } finally {
      enqueueSnackbar(t("studymanager:savedatasuccess"), {
        variant: "success",
      });
      loadFileData();
    }
  };

  const handleUpdate = async (change: CellChange[], source: string) => {
    if (source !== "loadData" && source !== "updateData") {
      try {
        const operations = slice(change);
        await editMatrix(study, url, operations);
      } catch (e) {
        enqueueErrorSnackbar("marche pas", e as AxiosError);
      }
    }
  };

  useEffect(() => {
    loadFileData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Root>
      <Content>
        <Header>
          <Typography
            sx={{
              color: "text.primary",
              fontSize: "1.25rem",
              fontWeight: 400,
              lineHeight: 1.334,
            }}
          >
            {t("xpansion.timeSeries")}
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center" }}>
            {loaded && data && data.data?.length > 1 && (
              <ButtonGroup sx={{ mr: 2 }} variant="contained">
                <StyledButton
                  onClick={
                    toggleView ? undefined : () => setToggleView(!toggleView)
                  }
                  disabled={toggleView}
                >
                  <TableViewIcon sx={{ color: "text.main" }} />
                </StyledButton>
                <StyledButton
                  onClick={
                    toggleView ? () => setToggleView(!toggleView) : undefined
                  }
                  disabled={!toggleView}
                >
                  <BarChartIcon sx={{ color: "text.main" }} />
                </StyledButton>
              </ButtonGroup>
            )}
            <Button
              variant="outlined"
              color="primary"
              startIcon={<GetAppOutlinedIcon />}
              onClick={() => setOpenImportDialog(true)}
            >
              {t("global.import")}
            </Button>
          </Box>
        </Header>
        <Divider sx={{ width: "100%", mt: 2, mb: 4 }} />
        {!loaded && <SimpleLoader />}
        {loaded && data && data.data?.length > 1 ? (
          <EditableMatrix
            matrix={data}
            readOnly={false}
            toggleView={toggleView}
            onUpdate={handleUpdate}
          />
        ) : (
          loaded && (
            <NoContent
              title="matrix.matrixEmpty"
              callToAction={
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<GetAppOutlinedIcon />}
                  onClick={() => setOpenImportDialog(true)}
                >
                  {t("global.import")}
                </Button>
              }
            />
          )
        )}
      </Content>
      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          title={t("matrix.importnewmatrix")}
          dropzoneText={t("matrix.importhint")}
          onClose={() => setOpenImportDialog(false)}
          onImport={onImport}
        />
      )}
    </Root>
  );
}

export default StudyMatrixView;
