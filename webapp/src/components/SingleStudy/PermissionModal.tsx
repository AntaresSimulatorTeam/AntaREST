/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { createStyles, makeStyles, Theme, TextField, Typography, Chip, Select, MenuItem } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../Settings/GenericModal';
import { getGroups } from '../../services/api/user';
import { GroupDTO, StudyPublicMode } from '../../common/types';
import { updatePermission } from './utils';

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
  ownerContainer: {
    flex: '1',
    width: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: theme.spacing(2),
    marginBottom: theme.spacing(1),
  },
  owner: {
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
  select: {
    margin: theme.spacing(2),
  },
}));

interface PropTypes {
    open: boolean;
    studyId: string;
    ownerId: number;
    ownerName: string;
    groups: Array<GroupDTO>;
    publicMode: StudyPublicMode;
    name: string;
    updateInfos: (newOwnerId: number, newOwnerName: string, newGroups: Array<GroupDTO>, newPublicMode: StudyPublicMode,) => void;
    onClose: () => void;
}

const PermissionModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, studyId, ownerId, ownerName, groups, publicMode, name, updateInfos, onClose } = props;
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [currentOwner, setOwner] = useState<number>(ownerId);
  const [currentPublicMode, setCurrentPublicMode] = useState<StudyPublicMode>(publicMode);
  const [selectedGroupList, setSelectedGroupList] = useState<Array<GroupDTO>>(groups);

  const onSave = async () => {
    try {
      await updatePermission(studyId, ownerId, ownerName, groups, publicMode, currentOwner, selectedGroupList, currentPublicMode, updateInfos);
      enqueueSnackbar(t('singlestudy:onPermissionUpdate'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('singlestudy:onPermissionError'), { variant: 'error' });
    } finally {
      onClose();
    }
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
        const res = await getGroups();
        const filteredGroup = res.filter((item) => item.id !== 'admin');
        setGroupList(filteredGroup);
      } catch (e) {
        enqueueSnackbar(t('settings:groupsError'), { variant: 'error' });
      }
    };
    init();
    return () => {
      setGroupList([]);
    };
  }, [t, enqueueSnackbar]);

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={`${t('studymanager:permission')} - ${name}`}
    >
      <div className={classes.root}>
        <div className={classes.ownerContainer}>
          <TextField
            className={classes.owner}
            size="small"
            type="number"
            value={currentOwner}
            onChange={(event) => setOwner(Number(event.target.value))}
            label={t('singlestudy:owner')}
            variant="outlined"
          />
        </div>
        <div className={classes.parameters}>
          <div className={classes.parameterHeader}>
            <Typography className={classes.parameterTitle}>
              {t('singlestudy:publicMode')}
            </Typography>
          </div>
          <Select
            value={currentPublicMode as string}
            onChange={(event: React.ChangeEvent<{ value: unknown }>) =>
              setCurrentPublicMode(event.target.value as StudyPublicMode)
          }
            label={t('singlestudy:publicMode')}
            className={classes.select}
          >
            <MenuItem value="NONE">
              NONE
            </MenuItem>
            <MenuItem value="READ">
              READ
            </MenuItem>
            <MenuItem value="EXECUTE">
              EXECUTE
            </MenuItem>
            <MenuItem value="EDIT">
              EDIT
            </MenuItem>
            <MenuItem value="FULL">
              FULL
            </MenuItem>
          </Select>
        </div>
        <div className={classes.parameters}>
          <div className={classes.parameterHeader}>
            <Typography className={classes.parameterTitle}>
              {t('singlestudy:groupsLabel')}
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
      </div>
    </GenericModal>
  );
};

export default PermissionModal;
