import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  IconButton,
  Tooltip,
  ButtonGroup,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import TableViewIcon from "@mui/icons-material/TableView";
import BarChartIcon from "@mui/icons-material/BarChart";
import { Code, StyledButton } from "./styles";
import { MatrixType } from "../../../../common/types";
import usePromiseWithSnackbarError from "../../../../hooks/usePromiseWithSnackbarError";
import OkDialog from "../OkDialog";
import EditableMatrix from "../../EditableMatrix";
import { getStudyMatrixIndex } from "../../../../services/api/matrix";
import SimpleLoader from "../../loaders/SimpleLoader";

type MatrixTypeWithId = MatrixType & { id?: string };

interface Props {
  studyId?: string;
  filename: string;
  content?: string | MatrixTypeWithId;
  loading?: boolean;
  onClose: () => void;
  isMatrix?: boolean;
  readOnly?: boolean;
}

function DataViewerDialog(props: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const {
    studyId,
    filename,
    content,
    onClose,
    isMatrix,
    loading,
    readOnly = true,
  } = props;
  const [toggleView, setToggleView] = useState(true);

  const { data: matrixIndex } = usePromiseWithSnackbarError(
    async () => {
      if (studyId) {
        return getStudyMatrixIndex(studyId);
      }
      return undefined;
    },
    {
      errorMessage: t("matrix.error.failedToRetrieveIndex"),
      deps: [studyId],
    }
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const copyId = async (matrixId: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(matrixId);
      enqueueSnackbar(t("data.success.matrixIdCopied"), {
        variant: "success",
      });
    } catch (e) {
      enqueueSnackbar(t("data.error.copyMatrixId"), { variant: "error" });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const renderContent = (data: MatrixTypeWithId | string) =>
    isMatrix ? (
      <Box width="100%" height="100%" p={2}>
        <EditableMatrix
          matrix={data as MatrixType}
          matrixTime={!!matrixIndex}
          matrixIndex={matrixIndex}
          readOnly={!!readOnly}
          toggleView={toggleView}
        />
      </Box>
    ) : (
      <Code>
        <code style={{ whiteSpace: "pre" }}>{data as string}</code>
      </Code>
    );

  return (
    <OkDialog
      open
      title={
        isMatrix ? (
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography
              sx={{ fontWeight: 500, fontSize: "1.25rem" }}
            >{`Matrix - ${filename}`}</Typography>
            {content && (content as MatrixTypeWithId).id && (
              <IconButton
                onClick={() =>
                  copyId((content as MatrixTypeWithId).id as string)
                }
                sx={{
                  ml: 1,
                  color: "action.active",
                }}
              >
                <Tooltip title={t("study.copyId") as string}>
                  <ContentCopyIcon sx={{ height: "20px", width: "20px" }} />
                </Tooltip>
              </IconButton>
            )}
            <ButtonGroup sx={{ ml: 1 }} variant="contained">
              <StyledButton onClick={() => setToggleView((prev) => !prev)}>
                {toggleView ? (
                  <BarChartIcon sx={{ color: "text.main" }} />
                ) : (
                  <TableViewIcon sx={{ color: "text.main" }} />
                )}
              </StyledButton>
            </ButtonGroup>
          </Box>
        ) : (
          filename
        )
      }
      contentProps={{
        sx: { p: 0, height: "60vh", overflow: "hidden" },
      }}
      fullWidth
      maxWidth="lg"
      okButtonText={t("button.close")}
      onOk={onClose}
    >
      {!!loading && <SimpleLoader />}
      {!!content && renderContent(content)}
    </OkDialog>
  );
}

DataViewerDialog.defaultProps = {
  isMatrix: false,
};

export default DataViewerDialog;
