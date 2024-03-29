import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import { Typography, Box, Button, Divider, Tooltip } from "@mui/material";
import UploadOutlinedIcon from "@mui/icons-material/UploadOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import InventoryIcon from "@mui/icons-material/Inventory";
import {
  MatrixEditDTO,
  MatrixStats,
  MatrixType,
  StudyMetadata,
} from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { getStudyData, importFile } from "../../../services/api/study";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import { editMatrix, getStudyMatrixIndex } from "../../../services/api/matrix";
import { Root, Content, Header } from "./style";
import SimpleLoader from "../loaders/SimpleLoader";
import SimpleContent from "../page/SimpleContent";
import EditableMatrix from "../EditableMatrix";
import ImportDialog from "../dialogs/ImportDialog";
import MatrixAssignDialog from "./MatrixAssignDialog";
import { downloadMatrix } from "../../../utils/matrixUtils";
import { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import { LoadingButton } from "@mui/lab";

const logErr = debug("antares:createimportform:error");

interface Props {
  study: StudyMetadata;
  url: string;
  columnsNames?: string[];
  rowNames?: string[];
  title?: string;
  computStats: MatrixStats;
  fetchFn?: fetchMatrixFn;
  disableEdit?: boolean;
  enablePercentDisplay?: boolean;
}

function MatrixInput({
  study,
  url,
  columnsNames,
  rowNames: initialRowNames,
  title,
  computStats,
  fetchFn,
  disableEdit,
  enablePercentDisplay,
}: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const [openMatrixAsignDialog, setOpenMatrixAsignDialog] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const {
    data: matrixData,
    isLoading,
    reload: reloadMatrix,
  } = usePromiseWithSnackbarError(fetchMatrixData, {
    errorMessage: t("data.error.matrix"),
    deps: [study.id, url, fetchFn],
  });

  const { data: matrixIndex } = usePromiseWithSnackbarError(
    async () => {
      if (fetchFn) {
        return matrixData?.index;
      }
      return getStudyMatrixIndex(study.id, url);
    },
    {
      errorMessage: t("matrix.error.failedToretrieveIndex"),
      deps: [study, url, fetchFn, matrixData],
    },
  );

  /**
   * If fetchFn is provided, custom row names (area names) are used from the matrixData's index property.
   * Otherwise, default row numbers and timestamps are displayed using initialRowNames.
   */
  const rowNames = fetchFn ? matrixIndex : initialRowNames;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  async function fetchMatrixData() {
    const res = fetchFn
      ? await fetchFn(study.id)
      : await getStudyData(study.id, url);
    if (typeof res === "string") {
      const fixed = res
        .replace(/NaN/g, '"NaN"')
        .replace(/Infinity/g, '"Infinity"');
      return JSON.parse(fixed);
    }
    return res;
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdate = async (change: MatrixEditDTO[], source: string) => {
    if (source !== "loadData" && source !== "updateData") {
      try {
        if (change.length > 0) {
          const sanitizedUrl = url.startsWith("/") ? url.substring(1) : url;
          await editMatrix(study.id, sanitizedUrl, change);
          enqueueSnackbar(t("matrix.success.matrixUpdate"), {
            variant: "success",
          });
        }
      } catch (e) {
        enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), e as AxiosError);
      }
    }
  };

  const handleImport = async (file: File) => {
    try {
      await importFile(file, study.id, url);
    } catch (e) {
      logErr("Failed to import file", file, e);
      enqueueErrorSnackbar(t("variants.error.import"), e as AxiosError);
    } finally {
      enqueueSnackbar(t("variants.success.import"), {
        variant: "success",
      });
      reloadMatrix();
    }
  };

  const handleDownload = async (matrixData: MatrixType, fileName: string) => {
    setIsDownloading(true);

    // Re-fetch to get latest data
    const data = await fetchMatrixData();
    downloadMatrix(data, fileName);

    setIsDownloading(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
            {title || t("xpansion.timeSeries")}
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Button
              sx={{
                mx: 2,
              }}
              variant="outlined"
              color="primary"
              onClick={() => setOpenMatrixAsignDialog(true)}
            >
              <Tooltip title={t("data.assignMatrix") as string}>
                <InventoryIcon />
              </Tooltip>
            </Button>

            <Button
              variant="outlined"
              color="primary"
              startIcon={<UploadOutlinedIcon />}
              onClick={() => setOpenImportDialog(true)}
            >
              {t("global.import")}
            </Button>

            {matrixData?.columns?.length >= 1 && (
              <LoadingButton
                sx={{
                  ml: 2,
                }}
                loadingPosition="start"
                loading={isDownloading}
                variant="outlined"
                color="primary"
                startIcon={<DownloadOutlinedIcon />}
                onClick={() =>
                  handleDownload(
                    matrixData,
                    `matrix_${study.id}_${url.replace("/", "_")}`,
                  )
                }
              >
                {t("global.download")}
              </LoadingButton>
            )}
          </Box>
        </Header>
        <Divider sx={{ width: "100%", mt: 1, mb: 2 }} />
        {isLoading && <SimpleLoader />}
        {!isLoading && matrixData?.columns?.length >= 1 && matrixIndex ? (
          <EditableMatrix
            matrix={matrixData}
            matrixTime={!rowNames}
            matrixIndex={matrixIndex}
            columnsNames={columnsNames}
            rowNames={rowNames}
            readOnly={!!disableEdit}
            onUpdate={handleUpdate}
            computStats={computStats}
            isPercentDisplayEnabled={enablePercentDisplay}
          />
        ) : (
          !isLoading && (
            <SimpleContent
              title="matrix.message.matrixEmpty"
              callToAction={
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<UploadOutlinedIcon />}
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
          title={t("matrix.importNewMatrix")}
          dropzoneText={t("matrix.message.importHint")}
          onClose={() => setOpenImportDialog(false)}
          onImport={handleImport}
        />
      )}
      {openMatrixAsignDialog && (
        <MatrixAssignDialog
          study={study}
          path={url}
          open={openMatrixAsignDialog}
          onClose={() => {
            setOpenMatrixAsignDialog(false);
            reloadMatrix();
          }}
        />
      )}
    </Root>
  );
}

export default MatrixInput;
