/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { createStyles, makeStyles, Theme, TextField, Typography, Button, Checkbox, Chip } from '@material-ui/core';
import AddBoxIcon from '@material-ui/icons/AddBox';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../../components/Settings/GenericModal';
import { getGroups } from '../../../services/api/user';
import { GroupDTO, MatrixMetadataDTO } from '../../../common/types';
import { KeyValue, Metadata } from '../../../components/Data/KeyValue';
import { saveMatrix } from './utils';

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
    marginBottom: theme.spacing(3),
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
  metadataList: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
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
}));

interface PropTypes {
    open: boolean;
    onNewDataUpdate: (newData: MatrixMetadataDTO) => void;
    data: MatrixMetadataDTO | undefined;
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
  const [metadataList, setMetadata] = useState<Array<Metadata>>([]);
  const [currentFile, setFile] = useState<File|undefined>();
  const [publicStatus, setPublic] = useState<boolean>(false);

  const onSave = async () => {
    let closeModal = true;
    try {
      const msg = await saveMatrix(name, publicStatus, metadataList, selectedGroupList, onNewDataUpdate, currentFile, data);
      enqueueSnackbar(t(msg), { variant: 'success' });
    } catch (e) {
      const error = e as Error;
      enqueueSnackbar(t(error.message), { variant: 'error' });
      if (error.message === 'data:fileNotUploaded' || error.message === 'data:emptyName') closeModal = false;
    } finally {
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

  const addNewMetadata = () => {
    setMetadata(metadataList.concat({ key: '', value: '', editStatus: true }));
  };

  const onMetadataChange = (newMetadata: Metadata, index: number): void => {
    if (index >= 0 && index < metadataList.length) {
      if (newMetadata.key.replace(/\s/g, '') && newMetadata.value.replace(/\s/g, '')) {
        if (metadataList.findIndex((item) => item.key === newMetadata.key && !item.editStatus) < 0) {
          let tmpList: Array<Metadata> = [];
          tmpList = tmpList.concat(metadataList);
          tmpList[index] = { ...newMetadata, editStatus: false };
          setMetadata(tmpList);
        }
      }
    }
  };

  const metadataEditToogle = (index: number): void => {
    let tmpList: Array<Metadata> = [];
    tmpList = tmpList.concat(metadataList);
    tmpList[index] = { ...metadataList[index], editStatus: !metadataList[index].editStatus };
    setMetadata(tmpList);
  };

  const onMetadataDeletion = (index: number): void => {
    setMetadata(metadataList.filter((value, idx) => idx !== index));
  };

  const onGroupClick = (add: boolean, item: GroupDTO) => {
    if (add) {
      setSelectedGroupList(selectedGroupList.concat([item]));
    } else {
      setSelectedGroupList(selectedGroupList.filter((elm) => item.id !== elm.id));
    }
  };

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
          setMetadata(Object.keys(data.metadata).map((elm) => ({ key: elm, value: data.metadata[elm], editStatus: false })));
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
      handleClose={onClose}
      handleSave={onSave}
      title={data ? data.name : t('data:newMatrixTitle')}
    >
      <div className={classes.root}>
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
                </label>
              </div>
              )
            }
        </div>
        <div className={classes.parameters}>
          <div className={classes.parameterHeader}>
            <Typography className={classes.parameterTitle}>
              {t('data:metadata')}
            </Typography>
            <AddBoxIcon
              className={classes.addElement}
              onClick={addNewMetadata}
            />
          </div>
          <div className={classes.metadataList}>
            {
              metadataList.map((element: Metadata, index: number) => (
                <KeyValue
                  // eslint-disable-next-line react/no-array-index-key
                  key={`${element.key}_${index}`}
                  index={index}
                  metadata={element}
                  onConfirmation={onMetadataChange}
                  editToogle={metadataEditToogle}
                  onDeletion={onMetadataDeletion}
                />
              ))
            }
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
