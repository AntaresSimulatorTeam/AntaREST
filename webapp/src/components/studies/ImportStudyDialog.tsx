import { useEffect, useState } from "react";
import * as R from "ramda";
import { AxiosError } from "axios";
import { Box, LinearProgress, Paper, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import Dropzone from "react-dropzone";
import { useSnackbar } from "notistack";
import { useMountedState } from "react-use";
import { createStudy } from "../../redux/ducks/studies";
import BasicDialog, { BasicDialogProps } from "../common/dialogs/BasicDialog";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import { useAppDispatch } from "../../redux/hooks";

interface Props {
  open: BasicDialogProps["open"];
  onClose: VoidFunction;
}

function ImportStudyDialog(props: Props) {
  const { open, onClose } = props;
  const [t] = useTranslation();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(-1);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const isMounted = useMountedState();
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (isUploading) {
      const listener = (e: BeforeUnloadEvent) => {
        // eslint-disable-next-line no-param-reassign
        e.returnValue = "Study Import";
      };

      window.addEventListener("beforeunload", listener);

      return () => {
        window.removeEventListener("beforeunload", listener);
      };
    }
  }, [isUploading]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDrop = (acceptedFiles: File[]) => {
    const fileToUpload = R.last(acceptedFiles);

    if (fileToUpload) {
      setIsUploading(true);
      setUploadProgress(0);

      dispatch(
        createStudy({
          file: fileToUpload,
          onUploadProgress: (progress) => {
            if (isMounted()) {
              setUploadProgress(progress);
            }
          },
        })
      )
        .unwrap()
        .then(() => {
          enqueueSnackbar(
            t("global:studies.success.import", { uploadFile: fileToUpload.name }),
            { variant: "success" }
          );
          if (isMounted()) {
            onClose();
          }
        })
        .catch((err) => {
          enqueueErrorSnackbar(
            t("global:studies.error.import", { uploadFile: fileToUpload.name }),
            err as AxiosError
          );
        })
        .finally(() => {
          if (isMounted()) {
            setIsUploading(false);
            setUploadProgress(-1);
          }
        });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      open={open}
      onClose={uploadProgress > -1 ? undefined : onClose}
      title={t("global:studies.importnewstudy")}
    >
      <Box sx={{ p: 2 }}>
        {uploadProgress > -1 ? (
          <LinearProgress
            variant={
              uploadProgress > 2 && uploadProgress < 98
                ? "determinate"
                : "indeterminate"
            }
            value={uploadProgress}
          />
        ) : (
          <Dropzone onDrop={handleDrop} disabled={isUploading} multiple={false}>
            {({ getRootProps, getInputProps }) => (
              <Paper sx={{ border: "1px dashed grey", p: 4 }}>
                <div {...getRootProps()}>
                  <input {...getInputProps()} />
                  <Typography sx={{ cursor: "pointer" }}>
                    {t("global:studies.importhint")}
                  </Typography>
                </div>
              </Paper>
            )}
          </Dropzone>
        )}
      </Box>
    </BasicDialog>
  );
}

export default ImportStudyDialog;
