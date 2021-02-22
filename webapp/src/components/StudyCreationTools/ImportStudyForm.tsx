import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Button, LinearProgress } from '@material-ui/core';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { getStudyData, importStudy } from '../../services/api/study';
import { getStudyIdFromUrl, convertStudyDtoToMetadata } from '../../services/utils';
import { addStudies } from '../../ducks/study';
import { StudyMetadata } from '../../common/types';
import { addUpload, updateUpload, completeUpload } from '../../ducks/upload';
import { AppState } from '../../App/reducers';

const logErr = debug('antares:createstudyform:error');

interface Inputs {
  study: FileList;
}

const mapState = (state: AppState) => ({ uploads: state.upload.uploads });

const mapDispatch = ({
  addStudy: (study: StudyMetadata) => addStudies([study]),
  createUpload: (name: string) => addUpload(name),
  updateUploadCompletion: (id: string, completion: number) => updateUpload(id, completion),
  endUpload: (id: string) => completeUpload(id),
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  useStyles: () => Record<'button' | 'root' | 'input', string>;
}
type PropTypes = PropsFromRedux & OwnProps;


const ImportStudyForm = (props: PropTypes) => {
  const [t] = useTranslation();
  const { useStyles, addStudy, uploads, createUpload, updateUploadCompletion, endUpload } = props;
  const classes = useStyles();
  const { register, handleSubmit } = useForm<Inputs>();
  const [uploadProgress, setUploadProgress] = useState<number>();

  const onSubmit = async (data: Inputs) => {
    if (data.study && data.study.length === 1) {
      const uploadId = createUpload('Study import');
      try {
        const res = await importStudy(data.study[0], (completion) => { updateUploadCompletion(uploadId, completion); setUploadProgress(completion); });
        const sid = getStudyIdFromUrl(res);
        const metadata = await getStudyData(sid, 'study/antares', 1);
        addStudy(convertStudyDtoToMetadata(sid, metadata));
      } catch (e) {
        logErr('Failed to import study', data.study, e);
      } finally {
        setUploadProgress(undefined);
        endUpload(uploadId);
      }
    }
  };

  return (
    <form className={classes.root} onSubmit={handleSubmit(onSubmit)}>
      <Button className={classes.button} type="submit" variant="outlined" color="primary">{t('main:import')}</Button>
      <input className={classes.input} type="file" name="study" accept="application/zip" ref={register({ required: true })} />
      {uploadProgress && <LinearProgress style={{ flexGrow: 1 }} variant="determinate" value={uploadProgress} />}
    </form>
  );
};

export default connector(ImportStudyForm);
