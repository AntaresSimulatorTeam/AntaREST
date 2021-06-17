/* eslint-disable @typescript-eslint/camelcase */
import React, { useState, useEffect } from 'react';
import { createStyles, makeStyles, Theme, TextField, Typography } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import Checkbox from '@material-ui/core/Checkbox';
import GenericModal from '../../../../../components/Settings/GenericModal';
import GroupsAssignmentView from '../../../../../components/Settings/GroupsAssignmentView';
import { getGroups } from '../../../../../services/api/user';
import { GroupDTO, RoleType, RoleDTO, BotDTO, JWTGroup } from '../../../../../common/types';
import { saveToken } from './utils';

const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: theme.spacing(1),
    paddingLeft: theme.spacing(3),
  },
  idFields: {
    width: '70%',
    height: '30px',
    boxSizing: 'border-box',
    margin: theme.spacing(2),
  },
  checkbox: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    margin: theme.spacing(2),
  },
}));

interface PropTypes {
    open: boolean;
    userGroups?: Array<JWTGroup>;
    onNewTokenCreation: (newToken: string, newBot: BotDTO) => void;
    onClose: () => void;
}

const TokenCreationModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, userGroups, onNewTokenCreation, onClose } = props;
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [roleList, setRoleList] = useState<Array<RoleDTO>>([]);
  const [tokenName, setTokenName] = useState<string>('');
  const [checked, setChecked] = useState<boolean>(false);
  const [selectedGroup, setActiveGroup] = useState<GroupDTO>();

  const onChange = (group: GroupDTO) => {
    setActiveGroup(group);
  };

  const addRoleToList = () => {
    // 1) Look if role is already added to list
    if (selectedGroup && !roleList.find((item) => item.group_id === selectedGroup.id)) {
      // 2) Create a new role with type == READER
      const newRole: RoleDTO = {
        group_id: selectedGroup.id,
        group_name: selectedGroup.name,
        identity_id: -1,
        type: RoleType.READER, // READER by default
      };
      // 3) Add the role in roleList
      setRoleList(roleList.concat([newRole]));
    }
  };

  const deleteRoleFromList = (groupId: string) => {
    // Delete role from roleList
    const tmpList = roleList.filter((item) => item.group_id !== groupId);
    setRoleList(tmpList);
  };

  // Update Role in roleList
  const updateRoleFromList = (groupId: string, type: RoleType) => {
    // 1) Find the role
    const tmpList: Array<RoleDTO> = ([] as Array<RoleDTO>).concat(roleList);
    const index = roleList.findIndex((item) => item.group_id === groupId);
    if (index >= 0) {
      // 2) Update role in roleList
      tmpList[index].type = type;
      setRoleList(tmpList);
    }
  };

  const onSave = async () => {
    try {
      // 1) Create new token
      await saveToken(tokenName,
        checked,
        roleList,
        onNewTokenCreation);
      enqueueSnackbar(t('settings:onTokenCreation'), { variant: 'success' });
      onClose();
    } catch (e) {
      enqueueSnackbar(t('settings:onTokenSaveError'), { variant: 'error' });
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        // Get list of all groups and add it to groupList or locally from access_token
        const groups = await getGroups();
        const filteredGroup = groups.filter((item) => item.id !== 'admin');
        setGroupList(filteredGroup);
        if (filteredGroup.length > 0) setActiveGroup(filteredGroup[0]);
      } catch (e) {
        enqueueSnackbar(t('settings:tokensError'), { variant: 'error' });
      }
    };
    init();
  }, [t, enqueueSnackbar]);

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={t('settings:newTokenTitle')}
    >
      <div className={classes.infos}>
        <TextField
          className={classes.idFields}
          value={tokenName}
          onChange={(event) => setTokenName(event.target.value as string)}
          label={t('settings:tokenNameLabel')}
          variant="outlined"
        />
        <div className={classes.checkbox}>
          <Checkbox
            checked={checked}
            onChange={() => setChecked(!checked)}
            inputProps={{ 'aria-label': 'primary checkbox' }}
          />
          <Typography>
            {t('settings:linkTokenLabel')}
          </Typography>
        </div>
      </div>

      {
            !!selectedGroup && (
            <GroupsAssignmentView
              groupsList={groupList}
              roleList={roleList}
              userGroups={userGroups}
              selectedGroup={selectedGroup}
              onChange={onChange}
              addRole={addRoleToList}
              deleteRole={deleteRoleFromList}
              updateRole={updateRoleFromList}
            />
            )}
    </GenericModal>
  );
};

TokenCreationModal.defaultProps = {
  userGroups: [],
};

export default TokenCreationModal;
