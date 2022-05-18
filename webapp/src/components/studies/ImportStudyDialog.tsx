import { useEffect, useState } from "react";
import * as R from "ramda";
import { AxiosError } from "axios";
import { Box, LinearProgress, Paper, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { connect, ConnectedProps } from "react-redux";
import Dropzone from "react-dropzone";
import { useSnackbar } from "notistack";
import { usePromise, useMountedState } from "react-use";
import { createStudy } from "../../redux/ducks/studies";
import BasicDialog, { BasicDialogProps } from "../common/dialogs/BasicDialog";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";

const mapDispatch = {
  addStudy: createStudy,
};

const connector = connect(null, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux & BasicDialogProps;

function ImportStudyDialog(props: PropTypes) {
  const { open, onClose, addStudy } = props;
  const [t] = useTranslation();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(-1);
  const mounted = usePromise();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const isMounted = useMountedState();

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

  const handleDrop = async (acceptedFiles: File[]) => {
    const fileToUpload = R.last(acceptedFiles);

    if (fileToUpload) {
      setIsUploading(true);
      setUploadProgress(0);

      try {
        await mounted(
          addStudy({
            file: fileToUpload,
            onUploadProgress: (progress) => {
              if (isMounted()) {
                setUploadProgress(progress);
              }
            },
          }).unwrap()
        );

        enqueueSnackbar(
          t("studymanager:importsuccess", { uploadFile: fileToUpload.name }),
          { variant: "success" }
        );
        (onClose as () => void)?.();
      } catch (e) {
        enqueueErrorSnackbar(
          t("studymanager:importfailure", { uploadFile: fileToUpload.name }),
          e as AxiosError
        );
      } finally {
        setIsUploading(false);
        setUploadProgress(-1);
      }
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      open={open}
      onClose={uploadProgress > -1 ? undefined : onClose}
      title={t("studymanager:importnewstudy")}
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
                    {t("studymanager:importhint")}
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

export default connector(ImportStudyDialog);
