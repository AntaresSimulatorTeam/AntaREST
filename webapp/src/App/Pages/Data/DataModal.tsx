/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../../components/Settings/GenericModal';
import GroupsAssignmentView from '../../../components/Settings/GroupsAssignmentView';
import { getGroups, getUserInfos } from '../../../services/api/user';
import { GroupDTO, RoleType, RoleDTO, MatrixMetadataDTO, UserInfo } from '../../../common/types';


const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: theme.spacing(2),
  },
  idFields: {
    width: '70%',
    height: '30px',
    boxSizing: 'border-box',
    margin: theme.spacing(2),
  },
}));

interface PropTypes {
    open: boolean;
    onNewDataCreation: (newData: MatrixMetadataDTO) => void;
    data: MatrixMetadataDTO | undefined;
    userId: number|undefined;
    onClose: () => void;
}

const DataModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, onNewDataCreation, onClose, data, userId } = props;
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [name, setName] = useState<string>('');
  const [selectedGroup, setActiveGroup] = useState<GroupDTO>();

  const onChange = (group: GroupDTO) => {
    setActiveGroup(group);
  };


  const onSave = async () => {
    try {
      //await saveUser(username, password, roleList, onNewUserCreaion, userInfos);
      //if (userInfos) enqueueSnackbar(t('settings:onUserUpdate'), { variant: 'success' });
      //else enqueueSnackbar(t('settings:onUserCreation'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('data:onMatrixSaveError'), { variant: 'error' });
    }
    onClose();
  };

  useEffect(() => {
    const init = async () => {
      try {
        // 1) Get list of all groups and add it to groupList
        const groups = await getGroups();
        const filteredGroup = groups.filter((item) => item.id !== 'admin');
        setGroupList(filteredGroup);

        if (filteredGroup.length > 0) setActiveGroup(filteredGroup[0]);

      } catch (e) {
        enqueueSnackbar(t('settings:groupsError'), { variant: 'error' });
      }
    };
    init();
    return () => {
      setGroupList([]);
      setActiveGroup(undefined);
    };
  }, [data, t, enqueueSnackbar]);

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={data ? data.name : t('data:newMatrixTitle')}
    >
      {
                !data &&
                (
                <div className={classes.infos}>
                  <TextField
                    className={classes.idFields}
                    value={name}
                    onChange={(event) => setName(event.target.value as string)}
                    label={t('data:matrixNameLabel')}
                    variant="outlined"
                  />
                </div>
                )

            }
    </GenericModal>
  );
};

export default DataModal;
