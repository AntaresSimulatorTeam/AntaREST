import { useState } from "react";
import * as R from "ramda";
import { AxiosError } from "axios";
import { Box, LinearProgress, Paper, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { connect, ConnectedProps } from "react-redux";
import Dropzone from "react-dropzone";
import { useSnackbar } from "notistack";
import { usePromise } from "react-use";
import { getStudyMetadata, importStudy } from "../../services/api/study";
import { addStudies } from "../../redux/ducks/study";
import { StudyMetadata } from "../../common/types";
import {
  addUpload,
  updateUpload,
  completeUpload,
} from "../../redux/ducks/upload";
import { AppState } from "../../redux/ducks";
import BasicDialog, { BasicDialogProps } from "../common/dialogs/BasicDialog";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";

const mapState = (state: AppState) => ({ uploads: state.upload.uploads });

const mapDispatch = {
  addStudy: (study: StudyMetadata) => addStudies([study]),
  createUpload: (name: string) => addUpload(name),
  updateUploadCompletion: (id: string, completion: number) =>
    updateUpload(id, completion),
  endUpload: (id: string) => completeUpload(id),
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
type PropTypes = PropsFromRedux & BasicDialogProps;

function ImportStudyDialog(props: PropTypes) {
  const {
    open,
    onClose,
    addStudy,
    createUpload,
    updateUploadCompletion,
    endUpload,
  } = props;
  const [t] = useTranslation();
  const [uploadProgress, setUploadProgress] = useState<number>();
  const mounted = usePromise();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const onDrop = async (acceptedFiles: Array<File>) => {
    const fileToUpload = R.last(acceptedFiles);
    if (fileToUpload) {
      const uploadId = createUpload("Study import");
      try {
        const sid = await mounted(
          importStudy(fileToUpload, (completion) => {
            updateUploadCompletion(uploadId, completion);
            setUploadProgress(completion);
          })
        );
        const metadata = await mounted(getStudyMetadata(sid));
        addStudy(metadata);
        enqueueSnackbar(
          t("studymanager:importsuccess", { uploadFile: fileToUpload.name }),
          {
            variant: "success",
          }
        );
        (onClose as () => void)?.();
      } catch (e) {
        enqueueErrorSnackbar(
          t("studymanager:importfailure", {
            uploadFile: fileToUpload.name,
          }),
          e as AxiosError
        );
      } finally {
        setUploadProgress(undefined);
        endUpload(uploadId);
      }
    }
  };

  return (
    <BasicDialog
      open={open}
      onClose={uploadProgress !== undefined ? undefined : onClose}
      title={t("studymanager:importnewstudy")}
    >
      <Box sx={{ p: 2 }}>
        {uploadProgress !== undefined ? (
          <LinearProgress
            variant={
              uploadProgress > 2 && uploadProgress < 98
                ? "determinate"
                : "indeterminate"
            }
            value={uploadProgress}
          />
        ) : (
          <Dropzone onDrop={onDrop}>
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
