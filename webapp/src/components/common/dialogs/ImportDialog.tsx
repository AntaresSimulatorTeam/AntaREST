import { useEffect, useState } from "react";
import * as R from "ramda";
import { Box, LinearProgress, Paper, Typography } from "@mui/material";
import Dropzone from "react-dropzone";
import { useMountedState } from "react-use";
import { useTranslation } from "react-i18next";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";

interface Props {
  open: BasicDialogProps["open"];
  title?: string;
  dropzoneText?: string;
  onClose: VoidFunction;
  onImport: (
    file: File,
    onUploadProgress: (progress: number) => void
  ) => Promise<void>;
}

function ImportDialog(props: Props) {
  const { open, title, dropzoneText, onClose, onImport } = props;
  const [t] = useTranslation();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(-1);
  const isMounted = useMountedState();

  useEffect(() => {
    if (isUploading) {
      const listener = (e: BeforeUnloadEvent) => {
        // eslint-disable-next-line no-param-reassign
        e.returnValue = "Import";
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
        await onImport(fileToUpload, (progress) => {
          if (isMounted()) {
            setUploadProgress(progress);
          }
        });

        if (isMounted()) {
          onClose();
        }
      } catch {
        // noop
      } finally {
        if (isMounted()) {
          setIsUploading(false);
          setUploadProgress(-1);
        }
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
      title={title || t("global.import")}
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
                    {dropzoneText || t("global.importHint")}
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

ImportDialog.defaultProps = {
  title: null,
  dropzoneText: null,
};

export default ImportDialog;
