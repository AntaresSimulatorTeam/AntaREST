/* eslint-disable react-hooks/exhaustive-deps */
import { PropsWithChildren } from "react";
import { useTranslation } from "react-i18next";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { Code } from "./styles";
import MatrixView from "../../MatrixView";
import { MatrixType } from "../../../../common/types";
import OkDialog from "../OkDialog";

type MatrixTypeWithId = MatrixType & { id?: string };

interface Props {
  data: {
    filename: string;
    content: string | MatrixTypeWithId;
  };
  onClose: () => void;
  isMatrix?: boolean;
}

function ReaderDialog(props: PropsWithChildren<Props>) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { data, onClose, isMatrix } = props;

  const copyId = (matrixId: string): void => {
    try {
      navigator.clipboard.writeText(matrixId);
      enqueueSnackbar(t("data:onMatrixIdCopySuccess"), { variant: "success" });
    } catch (e) {
      enqueueSnackbar(t("data:onMatrixIdCopyError"), { variant: "error" });
    }
  };

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
                <Tooltip title={t("studymanager:copyID") as string}>
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
      okButtonText={t("main:closeButton")}
    >
      {isMatrix === true ? (
        <Box width="100%" height="100%" p={2}>
          <MatrixView matrix={data.content as MatrixType} readOnly />
        </Box>
      ) : (
        <Code>
          <code style={{ whiteSpace: "pre" }}>{data.content as string}</code>
        </Code>
      )}
    </OkDialog>
  );
}

ReaderDialog.defaultProps = {
  isMatrix: false,
};

export default ReaderDialog;
