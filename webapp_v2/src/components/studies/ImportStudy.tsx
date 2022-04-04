import React, { useRef, useState } from "react";
import { Button, LinearProgress } from "@mui/material";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import debug from "debug";
import { connect, ConnectedProps } from "react-redux";
import GetAppOutlinedIcon from "@mui/icons-material/GetAppOutlined";
import { getStudyMetadata, importStudy } from "../../services/api/study";
import { addStudies } from "../../store/study";
import { StudyMetadata } from "../../common/types";
import { addUpload, updateUpload, completeUpload } from "../../store/upload";
import { AppState } from "../../store/reducers";

const logErr = debug("antares:createstudyform:error");

interface Inputs {
  study: FileList;
}

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
type PropTypes = PropsFromRedux;

function ImportStudyForm(props: PropTypes) {
  const [t] = useTranslation();
  const { addStudy, createUpload, updateUploadCompletion, endUpload } = props;
  const { register, handleSubmit } = useForm<Inputs>();
  const [uploadProgress, setUploadProgress] = useState<number>();
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onSubmit = async (data: Inputs) => {
    if (data.study && data.study.length === 1) {
      const uploadId = createUpload("Study import");
      try {
        const sid = await importStudy(data.study[0], (completion) => {
          updateUploadCompletion(uploadId, completion);
          setUploadProgress(completion);
        });
        const metadata = await getStudyMetadata(sid);
        addStudy(metadata);
      } catch (e) {
        logErr("Failed to import study", data.study, e);
      } finally {
        setUploadProgress(undefined);
        endUpload(uploadId);
      }
    }
  };

  const onButtonClick = () => {
    if (inputRef.current) {
      inputRef.current.click();
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Button
        variant="outlined"
        type="submit"
        color="primary"
        startIcon={<GetAppOutlinedIcon />}
        onClick={onButtonClick}
      >
        {t("main:import")}
      </Button>
      {/* eslint-disable-next-line react/jsx-props-no-spreading */}
      <input
        style={{ display: "none" }}
        type="file"
        accept="application/zip"
        {...register("study", { required: true })}
        ref={(e) => {
          inputRef.current = e;
        }}
      />
      {uploadProgress && (
        <LinearProgress
          style={{ flexGrow: 1 }}
          variant="determinate"
          value={uploadProgress}
        />
      )}
    </form>
  );
}

export default connector(ImportStudyForm);
