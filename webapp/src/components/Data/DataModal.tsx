/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { createStyles, makeStyles, Theme, TextField, Typography, Button, Checkbox, Chip, Tooltip, CircularProgress } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import clsx from 'clsx';
import GenericModal from '../ui/GenericModal';
import { getGroups } from '../../services/api/user';
import { GroupDTO, MatrixDataSetDTO } from '../../common/types';
import { loaderStyle, saveMatrix } from './utils';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflowY: 'auto',
    overflowX: 'hidden',
    position: 'relative',
  },
  mandatoryInfos: {
    flex: '1',
    width: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: theme.spacing(2),
    marginBottom: theme.spacing(1),
  },
  info: {
    width: '400px',
    height: '30px',
    boxSizing: 'border-box',
    margin: theme.spacing(2),
  },
  parameters: {
    flex: '1',
    width: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    marginBottom: theme.spacing(2),
  },
  parameterHeader: {
    width: '100%',
    height: '40px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    paddingLeft: theme.spacing(2),
    boxSizing: 'border-box',
  },
  parameterTitle: {
    color: theme.palette.primary.main,
    marginRight: theme.spacing(1),
    fontWeight: 'bold',
  },
  input: {
    display: 'none',
  },
  button: {
    padding: theme.spacing(1),
    height: '30px',
    '&:hover': {
      borderColor: theme.palette.secondary.main,
      color: theme.palette.secondary.main,
    },
    marginRight: theme.spacing(1),
  },
  filename: {
    color: theme.palette.primary.main,
  },
  uploadLabel: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  addElement: {
    width: '24px',
    height: '24px',
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
    cursor: 'pointer',
  },
  groupManagement: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    flexWrap: 'wrap',
    '& > *': {
      margin: theme.spacing(0.5),
    },
  },
  ...loaderStyle,
}));

interface PropTypes {
    open: boolean;
    onNewDataUpdate: (newData: MatrixDataSetDTO) => void;
    data: MatrixDataSetDTO | undefined;
    onClose: () => void;
}

const DataModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, onNewDataUpdate, onClose, data } = props;
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [selectedGroupList, setSelectedGroupList] = useState<Array<GroupDTO>>([]);
  const [name, setName] = useState<string>('');
  const [isJson, setIsJson] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [currentFile, setFile] = useState<File|undefined>();
  const [importing, setImporting] = useState(false);
  const [publicStatus, setPublic] = useState<boolean>(false);

  const onSave = async () => {
    let closeModal = true;
    try {
      setImporting(true);
      const msg = await saveMatrix(name, publicStatus, selectedGroupList, onNewDataUpdate, currentFile, data, isJson, setUploadProgress);
      enqueueSnackbar(t(msg), { variant: 'success' });
    } catch (e) {
      const error = e as Error;
      enqueueSnackbar(t(error.message), { variant: 'error' });
      if (error.message === 'data:fileNotUploaded' || error.message === 'data:emptyName') closeModal = false;
    } finally {
      setImporting(false);
      if (closeModal) onClose();
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const onUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { target } = e;
    if (target && target.files && target.files.length === 1) {
      setFile(target.files[0]);
    }
  };

  const onGroupClick = (add: boolean, item: GroupDTO) => {
    if (add) {
      setSelectedGroupList(selectedGroupList.concat([item]));
    } else {
      setSelectedGroupList(selectedGroupList.filter((elm) => item.id !== elm.id));
    }
  };

  const HelperIcon = React.forwardRef<HTMLInputElement>((p, ref) => {
    if (ref) {
      // eslint-disable-next-line react/jsx-props-no-spreading
      return <span {...p} style={{ marginLeft: '0.5em' }} ref={ref}><FontAwesomeIcon icon={['far', 'question-circle']} /></span>;
    }
    return <div />;
  });

  useEffect(() => {
    const init = async () => {
      try {
        const groups = await getGroups();
        const filteredGroup = groups.filter((item) => item.id !== 'admin');
        setGroupList(filteredGroup);

        if (data) {
          setSelectedGroupList(data.groups);
          setPublic(data.public);
          setName(data.name);
        }
      } catch (e) {
        enqueueSnackbar(t('settings:groupsError'), { variant: 'error' });
      }
    };
    init();
    return () => {
      setGroupList([]);
    };
  }, [data, t, enqueueSnackbar]);

  return (
    <GenericModal
      open={open}
      handleClose={importing ? undefined : onClose}
      handleSave={importing ? undefined : onSave}
      title={data ? data.name : t('data:newMatrixTitle')}
    >
      <div className={classes.root}>
        {
          importing && (
            <>
              <div className={classes.rootLoader}>
                {
                  uploadProgress < 100 ? (
                    <div className={classes.loaderContainer}>
                      <CircularProgress variant="determinate" className={classes.loaderWheel} value={uploadProgress} />
                      <div className={classes.loaderMessage}>{t('data:uploadingmatrix')}</div>
                    </div>
                  ) : (
                    <div className={classes.loaderContainer}>
                      <CircularProgress className={classes.loaderWheel} />
                      <div className={classes.loaderMessage}>{t('data:analyzingmatrix')}</div>
                    </div>
                  )
                }

              </div>
              <div className={clsx(classes.rootLoader, classes.shadow)} />
            </>
          )
        }
        <div className={classes.mandatoryInfos}>
          <TextField
            className={classes.info}
            size="small"
            value={name}
            onChange={(event) => setName(event.target.value as string)}
            label={t('data:matrixNameLabel')}
            variant="outlined"
          />
          {
              !data && (
              <div className={classes.info}>
                <input
                  className={classes.input}
                  id="upload-file"
                  accept=".csv, .txt, .zip"
                  onChange={onUpload}
                  type="file"
                />
                <label htmlFor="upload-file" className={classes.uploadLabel}>
                  <Button className={classes.button} variant="outlined" color="primary" component="span">
                    {t('data:upload')}
                  </Button>
                  <Typography noWrap className={classes.filename}>
                    {currentFile ? currentFile.name : t('data:choosefile')}
                  </Typography>
                  <Tooltip title={t('data:uploadHelp') as string} placement="top">
                    <HelperIcon />
                  </Tooltip>
                </label>
              </div>
              )
            }
        </div>
        <div className={classes.parameters}>
          <div className={classes.parameterHeader}>
            <Typography className={classes.parameterTitle}>
              {t('data:jsonFormat')}
            </Typography>
            <Checkbox
              checked={isJson}
              onChange={() => setIsJson(!isJson)}
              inputProps={{ 'aria-label': 'primary checkbox' }}
            />
          </div>
        </div>
        <div className={classes.parameters}>
          <div className={classes.parameterHeader}>
            <Typography className={classes.parameterTitle}>
              {t('data:publicLabel')}
            </Typography>
            <Checkbox
              checked={publicStatus}
              onChange={() => setPublic(!publicStatus)}
              inputProps={{ 'aria-label': 'primary checkbox' }}
            />
          </div>
        </div>
        {
            !publicStatus && (
            <div className={classes.parameters}>
              <div className={classes.parameterHeader}>
                <Typography className={classes.parameterTitle}>
                  {t('data:groupsLabel')}
                </Typography>
              </div>
              <div className={classes.groupManagement}>
                {
                  groupList.map((item) => {
                    const index = selectedGroupList.findIndex((elm) => item.id === elm.id);
                    if (index >= 0) {
                      return <Chip key={item.id} label={item.name} onClick={() => onGroupClick(false, item)} color="primary" />;
                    }
                    return <Chip key={item.id} label={item.name} onClick={() => onGroupClick(true, item)} />;
                  })
                }
              </div>
            </div>
            )}
      </div>
    </GenericModal>
  );
};

export default DataModal;
