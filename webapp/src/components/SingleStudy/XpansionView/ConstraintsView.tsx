import React from 'react';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Box,
} from '@material-ui/core';
import debug from 'debug';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import ImportForm from '../../ui/ImportForm';
import { XpansionConstraints } from './types';

const logErr = debug('antares:createimportform:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    main: {
      backgroundColor: 'white',
      width: '98%',
      height: '98%',
      display: 'flex',
      flexFlow: 'column nowrap',
      alignItems: 'center',
    },
    import: {
      display: 'flex',
      justifyContent: 'flex-end',
    },
    content: {
      flex: '1',
      padding: theme.spacing(2),
      width: '100%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      alignItems: 'flex-end',
      overflow: 'hidden',
      '&> code': {
        paddingLeft: theme.spacing(2),
        paddingRight: theme.spacing(2),
      },
    },
  }));

interface PropType {
    content: XpansionConstraints;
}

const ConstraintsView = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { content } = props;

  const onImport = async (file: File) => {
    try {
      console.log(file);
    } catch (e) {
      logErr('Failed to import file', file, e);
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtosavedata'), e as AxiosError);
    } finally {
      enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
    }
  };

  return (
    <Box>
      <Box className={classes.import}>
        <ImportForm text={t('main:import')} onImport={onImport} />
      </Box>
      <Box className={classes.main}>
        <div className={classes.content}>
          {Object.keys(content).map((item) => (<code>{content[item]}</code>))}
        </div>
      </Box>
    </Box>
  );
};

export default ConstraintsView;
