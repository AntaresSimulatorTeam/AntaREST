import React, { useState } from 'react';
import { AxiosError } from 'axios';
import {
  makeStyles,
  createStyles,
  Theme,
  Box,
  Typography,
  Divider,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
} from '@material-ui/core';
import debug from 'debug';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import VisibilityIcon from '@material-ui/icons/Visibility';
import DeleteIcon from '@material-ui/icons/Delete';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import ImportForm from '../../ui/ImportForm';
import ConfirmationModal from '../../ui/ConfirmationModal';

const logErr = debug('antares:createimportform:error');

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      overflow: 'hidden',
      width: '100%',
      flexGrow: 1,
      flexDirection: 'column',
    },
    main: {
      backgroundColor: 'white',
      width: '98%',
      height: '98%',
      display: 'flex',
      flexFlow: 'column nowrap',
      alignItems: 'center',
    },
    title: {
      color: theme.palette.primary.main,
      fontSize: '1.25rem',
      fontWeight: 400,
      lineHeight: 1.334,
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
      alignItems: 'flex-start',

    },
    divider: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(2),
    },
    table: {
      minWidth: 650,
    },
    buttons: {
      display: 'flex',
      flexDirection: 'row',
      justifyContent: 'flex-end',
      alignItems: 'center',
    },
    icon: {
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1),
      '&:hover': {
        color: theme.palette.secondary.main,
        cursor: 'pointer',
      },
    },
    delete: {
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1),
      color: theme.palette.error.light,
      '&:hover': {
        color: theme.palette.error.main,
        cursor: 'pointer',
      },
    },
  }));

interface PropType {
    title: string;
    content: Array<string>;
    onDelete: (filename: string) => Promise<void>;
    onRead: (filename: string) => Promise<void>;
    uploadFile: (file: File) => Promise<void>;
}

const XpansionTable = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { title, content, onDelete, onRead, uploadFile } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<string>('');

  const onImport = async (file: File) => {
    try {
      await uploadFile(file);
    } catch (e) {
      logErr('Failed to import file', file, e);
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtosavedata'), e as AxiosError);
    } finally {
      enqueueSnackbar(t('studymanager:savedatasuccess'), { variant: 'success' });
    }
  };

  return (
    <Box className={classes.root}>
      <Typography className={classes.title}>
        {title}
      </Typography>
      <Divider className={classes.divider} />
      <Box className={classes.import}>
        <ImportForm text={t('main:import')} onImport={onImport} />
      </Box>
      <Box className={classes.main}>
        <Box className={classes.content}>
          <TableContainer component={Box}>
            <Table className={classes.table} aria-label="simple table">
              <TableHead>
                <TableRow>
                  <TableCell>Nom du fichier</TableCell>
                  <TableCell align="right">Options</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {content.map((row) => (
                  <TableRow key={row}>
                    <TableCell component="th" scope="row">
                      {row}
                    </TableCell>
                    <TableCell align="right" className={classes.buttons}>
                      <VisibilityIcon className={classes.icon} color="primary" onClick={() => onRead(row)} />
                      <DeleteIcon className={classes.delete} color="primary" onClick={() => setOpenConfirmationModal(row)} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Box>
      {openConfirmationModal && openConfirmationModal.length > 0 && (
        <ConfirmationModal
          open={!!openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('xpansion:deleteFile')}
          handleYes={() => { onDelete(openConfirmationModal); setOpenConfirmationModal(''); }}
          handleNo={() => setOpenConfirmationModal('')}
        />
      )}
    </Box>
  );
};

export default XpansionTable;
