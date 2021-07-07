import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { Button, createStyles, LinearProgress, makeStyles, Theme } from '@material-ui/core';
import debug from 'debug';
import { importFile } from '../../../../services/api/study';

const logErr = debug('antares:createstudyform:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      marginTop: theme.spacing(2),
      marginBottom: theme.spacing(2),
      display: 'flex',
      alignItems: 'center',
    },
    button: {
      width: '100px',
      height: '30px',
      border: `2px solid ${theme.palette.primary.main}`,
      '&:hover': {
        border: `2px solid ${theme.palette.secondary.main}`,
        color: theme.palette.secondary.main,
      },
      fontWeight: 'bold',
    },
    input: {
      width: '200px',
      marginLeft: theme.spacing(2),
      marginRight: theme.spacing(2),
    },
  }));

interface Inputs {
    file: FileList;
}

interface PropTypes {
  path: string;
  study: string;
  callback: (file: File) => void;
}

const ImportForm = (props: PropTypes) => {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { path, study, callback } = props;
  const classes = useStyles();
  const { register, handleSubmit } = useForm<Inputs>();
  const [uploadProgress, setUploadProgress] = useState<number>();

  const onSubmit = async (data: Inputs) => {
    if (data.file && data.file.length === 1) {
      try {
        await importFile(data.file[0], study, path, (completion) => { setUploadProgress(completion); });
      } catch (e) {
        logErr('Failed to import file', data.file, e);
        enqueueSnackbar(t('studymanager:failtosavedata'), { variant: 'error' });
      } finally {
        setUploadProgress(undefined);
      }
      callback(data.file[0]);
    }
  };

  return (
    <form className={classes.root} onSubmit={handleSubmit(onSubmit)}>
      <Button className={classes.button} type="submit" variant="outlined" color="primary">{t('main:import')}</Button>
      <input className={classes.input} type="file" name="file" ref={register({ required: true })} />
      {uploadProgress && <LinearProgress style={{ flexGrow: 1 }} variant="determinate" value={uploadProgress} />}
    </form>
  );
};

export default ImportForm;
