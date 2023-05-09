import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import {
  Typography,
  Box,
  ButtonGroup,
  Button,
  Divider,
  Tooltip,
} from "@mui/material";
import TableViewIcon from "@mui/icons-material/TableView";
import BarChartIcon from "@mui/icons-material/BarChart";
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
import { Root, Content, Header, StyledButton } from "./style";
import SimpleLoader from "../loaders/SimpleLoader";
import SimpleContent from "../page/SimpleContent";
import EditableMatrix from "../EditableMatrix";
import ImportDialog from "../dialogs/ImportDialog";
import MatrixAssignDialog from "./MatrixAssignDialog";
import { downloadMatrix } from "../../../utils/matrixUtils";
import { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";

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
}: Props) {
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [toggleView, setToggleView] = useState(true);
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const [openMatrixAsignDialog, setOpenMatrixAsignDialog] = useState(false);

  const {
    data: matrixData,
    isLoading,
    reload: reloadMatrix,
  } = usePromiseWithSnackbarError(
    async () => {
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
    },
    {
      errorMessage: t("data.error.matrix"),
      deps: [study, url],
    }
  );

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
    }
  );

  /**
   * If fetchFn is provided, custom row names (area names) are used from the matrixData's index property.
   * Otherwise, default row numbers and timestamps are displayed using initialRowNames.
   */
  const rowNames = fetchFn ? matrixIndex : initialRowNames;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdate = async (change: MatrixEditDTO[], source: string) => {
    if (source !== "loadData" && source !== "updateData") {
      try {
        if (change.length > 0) {
          await editMatrix(study.id, url, change);
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

  const handleDownload = (matrixData: MatrixType, fileName: string): void => {
    downloadMatrix(matrixData, fileName);
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
            {!isLoading && matrixData?.columns?.length >= 1 && (
              <ButtonGroup variant="contained">
                <StyledButton onClick={() => setToggleView((prev) => !prev)}>
                  {toggleView ? (
                    <BarChartIcon sx={{ color: "text.main" }} />
                  ) : (
                    <TableViewIcon sx={{ color: "text.main" }} />
                  )}
                </StyledButton>
              </ButtonGroup>
            )}
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
              <Button
                sx={{
                  ml: 2,
                }}
                variant="outlined"
                color="primary"
                startIcon={<DownloadOutlinedIcon />}
                onClick={() =>
                  handleDownload(
                    matrixData,
                    `matrix_${study.id}_${url.replace("/", "_")}`
                  )
                }
              >
                {t("global.download")}
              </Button>
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
            toggleView={toggleView}
            onUpdate={handleUpdate}
            computStats={computStats}
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
