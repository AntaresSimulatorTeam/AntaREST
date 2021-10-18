/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import { createStyles, makeStyles, Theme, TextField, Typography, Chip, Select, MenuItem } from '@material-ui/core';
import Autocomplete from '@material-ui/lab/Autocomplete';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../ui/GenericModal';
import { getGroups, getUsers } from '../../services/api/user';
import { GroupDTO, StudyMetadataOwner, StudyPublicMode, UserDTO } from '../../common/types';
import { updatePermission } from './utils';
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';

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
    marginBottom: theme.spacing(2),
    padding: theme.spacing(2),
  },
  owner: {
    width: '400px',
    height: '30px',
    marginLeft: theme.spacing(1),
    boxSizing: 'border-box',
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
    paddingLeft: theme.spacing(1.5),
  },
  select: {
    margin: theme.spacing(2),
    marginTop: theme.spacing(0.5),
  },
}));

interface PropTypes {
    open: boolean;
    studyId: string;
    owner: StudyMetadataOwner;
    groups: Array<GroupDTO>;
    publicMode: StudyPublicMode;
    name: string;
    onClose: () => void;
}

const PermissionModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, studyId, groups, publicMode, name, owner, onClose } = props;
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [selectedOwner, setOwner] = useState<UserDTO>();
  const [userList, setUserList] = useState<Array<UserDTO>>([]);
  const [currentPublicMode, setCurrentPublicMode] = useState<StudyPublicMode>(publicMode);
  const [selectedGroupList, setSelectedGroupList] = useState<Array<GroupDTO>>(groups);

  const onSave = async () => {
    try {
      await updatePermission(studyId, groups, publicMode, owner, selectedOwner, selectedGroupList, currentPublicMode);
      enqueueSnackbar(t('singlestudy:onPermissionUpdate'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:onPermissionError'), e as AxiosError);
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
        const groupRes = await getGroups();
        const filteredGroup = groupRes.filter((item) => item.id !== 'admin');
        setGroupList(filteredGroup);

        const userRes = await getUsers();
        setUserList(userRes);
        const foundUser = userRes.find((elm) => elm.id === owner.id);
        if (foundUser) {
          setOwner(foundUser);
        }
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('settings:groupsError'), e as AxiosError);
      }
    };
    init();
    return () => {
      setGroupList([]);
    };
  }, [owner.id, t, enqueueSnackbar]);

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={`${t('studymanager:permission')} - ${name}`}
    >
      <div className={classes.root}>
        <div className={classes.ownerContainer}>
          <Autocomplete
            options={userList}
            getOptionLabel={(option) => option.name}
            className={classes.owner}
            value={selectedOwner || null}
            onChange={(event: any, newValue: UserDTO | null) => setOwner(newValue || undefined)}
            renderInput={(params) => (
              <TextField
                // eslint-disable-next-line react/jsx-props-no-spreading
                {...params}
                className={classes.owner}
                size="small"
                label={t('singlestudy:owner')}
                variant="outlined"
              />
            )}
          />
        </div>
        <div className={classes.parameters}>
          <div className={classes.parameterHeader}>
            <Typography className={classes.parameterTitle}>
              {t('singlestudy:publicMode')}
            </Typography>
          </div>
          <Select
            value={(currentPublicMode as string)}
            onChange={(event: React.ChangeEvent<{ value: unknown }>) =>
              setCurrentPublicMode(event.target.value as StudyPublicMode)
          }
            label={t('singlestudy:publicMode')}
            className={classes.select}
          >
            <MenuItem value="NONE">
              {t('singlestudy:nonePublicMode')}
            </MenuItem>
            <MenuItem value="READ">
              {t('singlestudy:readPublicMode')}
            </MenuItem>
            <MenuItem value="EXECUTE">
              {t('singlestudy:executePublicMode')}
            </MenuItem>
            <MenuItem value="EDIT">
              {t('singlestudy:editPublicMode')}
            </MenuItem>
            <MenuItem value="FULL">
              {t('singlestudy:fullPublicMode')}
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
