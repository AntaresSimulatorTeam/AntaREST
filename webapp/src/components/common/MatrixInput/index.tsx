import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import { Typography, Box, ButtonGroup, Button, Divider } from "@mui/material";
import TableViewIcon from "@mui/icons-material/TableView";
import BarChartIcon from "@mui/icons-material/BarChart";
import GetAppOutlinedIcon from "@mui/icons-material/GetAppOutlined";
import {
  MatrixEditDTO,
  MatrixStats,
  StudyMetadata,
} from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { getStudyData, importFile } from "../../../services/api/study";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import { editMatrix, getStudyMatrixIndex } from "../../../services/api/matrix";
import { Root, Content, Header, StyledButton } from "./style";
import SimpleLoader from "../loaders/SimpleLoader";
import NoContent from "../page/NoContent";
import EditableMatrix from "../EditableMatrix";
import ImportDialog from "../dialogs/ImportDialog";

const logErr = debug("antares:createimportform:error");

interface PropsType {
  study: StudyMetadata;
  url: string;
  columnsNames?: string[];
  title?: string;
  computStats: MatrixStats;
}

function MatrixInput(props: PropsType) {
  const { study, url, columnsNames, title, computStats } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [toggleView, setToggleView] = useState(true);
  const [openImportDialog, setOpenImportDialog] = useState(false);

  const {
    data,
    isLoading,
    reload: reloadMatrix,
  } = usePromiseWithSnackbarError(
    async () => {
      const res = await getStudyData(study.id, url);
      if (typeof res === "string") {
        const fixed = res.replace(/NaN/g, '"NaN"');
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
    () => getStudyMatrixIndex(study.id, url),
    {
      errorMessage: t("matrix.error.failedtoretrieveindex"),
      deps: [study, url],
    }
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdate = async (change: MatrixEditDTO[], source: string) => {
    if (source !== "loadData" && source !== "updateData") {
      try {
        if (change.length > 10) {
          throw new Error(t("matrix.error.tooManyUpdates"));
        }
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
            {!isLoading && data?.columns?.length > 1 && (
              <ButtonGroup sx={{ mr: 2 }} variant="contained">
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
              variant="outlined"
              color="primary"
              startIcon={<GetAppOutlinedIcon />}
              onClick={() => setOpenImportDialog(true)}
            >
              {t("global.import")}
            </Button>
          </Box>
        </Header>
        <Divider sx={{ width: "100%", mt: 2, mb: 3 }} />
        {isLoading && <SimpleLoader />}
        {!isLoading && data?.columns?.length > 1 ? (
          <EditableMatrix
            matrix={data}
            matrixTime
            matrixIndex={matrixIndex}
            columnsNames={columnsNames}
            readOnly={false}
            toggleView={toggleView}
            onUpdate={handleUpdate}
            computStats={computStats}
          />
        ) : (
          !isLoading && (
            <NoContent
              title="matrix.message.matrixEmpty"
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
          title={t("matrix.importNewMatrix")}
          dropzoneText={t("matrix.message.importHint")}
          onClose={() => setOpenImportDialog(false)}
          onImport={handleImport}
        />
      )}
    </Root>
  );
}

MatrixInput.defaultProps = {
  columnsNames: undefined,
  title: undefined,
};

export default MatrixInput;
