import { PropsWithChildren, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { AxiosError } from "axios";
import { Code } from "./styles";
import { MatrixType, MatrixIndex } from "../../../../common/types";
import OkDialog from "../OkDialog";
import EditableMatrix from "../../EditableMatrix";
import { getStudyMatrixIndex } from "../../../../services/api/matrix";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";

type MatrixTypeWithId = MatrixType & { id?: string };

interface Props {
  studyId: string;
  data: {
    filename: string;
    content: string | MatrixTypeWithId;
  };
  onClose: () => void;
  isMatrix?: boolean;
}

function DataViewerDialog(props: PropsWithChildren<Props>) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { studyId, data, onClose, isMatrix } = props;
  const [matrixIndex, setMatrixIndex] = useState<MatrixIndex>();

  const copyId = (matrixId: string): void => {
    try {
      navigator.clipboard.writeText(matrixId);
      enqueueSnackbar(t("data.success.matrixIdCopied"), {
        variant: "success",
      });
    } catch (e) {
      enqueueSnackbar(t("data.error.copyMatrixId"), { variant: "error" });
    }
  };

  const getMatrixIndex = async () => {
    try {
      const res = await getStudyMatrixIndex(studyId);
      setMatrixIndex(res);
    } catch (e) {
      enqueueErrorSnackbar(
        t("matrix.error.failedtoretrieveindex"),
        e as AxiosError
      );
    }
  };

  useEffect(() => {
    getMatrixIndex();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId]);

  return (
    <OkDialog
      open
      title={
        isMatrix ? (
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography
              sx={{ fontWeight: 500, fontSize: "1.25rem" }}
            >{`Matrix - ${data.filename}`}</Typography>
            {(data.content as MatrixTypeWithId).id && (
              <IconButton
                onClick={() =>
                  copyId((data.content as MatrixTypeWithId).id as string)
                }
                sx={{
                  mx: 1,
                  color: "action.active",
                }}
              >
                <Tooltip title={t("study.copyId") as string}>
                  <ContentCopyIcon sx={{ height: "20px", width: "20px" }} />
                </Tooltip>
              </IconButton>
            )}
          </Box>
        ) : (
          data.filename
        )
      }
      onOk={onClose}
      contentProps={{
        sx: { p: 0, height: "60vh", overflow: "hidden" },
      }}
      fullWidth
      maxWidth="lg"
      okButtonText={t("button.close")}
    >
      {isMatrix === true ? (
        <Box width="100%" height="100%" p={2}>
          <EditableMatrix
            matrix={data.content as MatrixType}
            matrixTime
            matrixIndex={matrixIndex}
            readOnly
          />
        </Box>
      ) : (
        <Code>
          <code style={{ whiteSpace: "pre" }}>{data.content as string}</code>
        </Code>
      )}
    </OkDialog>
  );
}

DataViewerDialog.defaultProps = {
  isMatrix: false,
};

export default DataViewerDialog;
