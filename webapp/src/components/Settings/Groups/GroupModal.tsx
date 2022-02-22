import React, { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import { createStyles, makeStyles, Theme, TextField, Select, MenuItem, Typography, Button } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import GenericModal from '../../ui/GenericModal';
import { RoleType, UserDTO, UserGroup, UserRoleDTO } from '../../../common/types';
import { menuItems } from './utils';
import { getUsers } from '../../../services/api/user';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';

const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing(3),
    marginBottom: theme.spacing(0),
  },
  idFields: {
    width: '70%',
    height: '30px',
    boxSizing: 'border-box',
    margin: theme.spacing(2),
  },
  select: {
    maxWidth: '400px',
    width: '100%',
  },
  roleSelect: {
    maxWidth: '400px',
  },
  addInfo: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    width: '70%',
    height: '50px',
    margin: theme.spacing(2, 0),
  },
  addText: {
    color: theme.palette.primary.main,
    textAlign: 'justify',
    fontSize: '1em',
    margin: 0,
    padding: 0,
  },
  userList: {
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    width: '70%',
    marginBottom: theme.spacing(2),
  },
  userSelect: {
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    marginRight: theme.spacing(3),
  },
  user: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    flex: 1,
  },
}));

interface PropTypes {
    isAdmin: boolean;
    open: boolean;
    onClose: () => void;
    onSave: (name: string, userList: Array<UserRoleDTO>) => void;
    group: UserGroup | undefined;
    userId: number | undefined;
}

const GroupModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, group, userId, isAdmin, onClose, onSave } = props;
  const [text, setText] = useState<string>('');
  const [userList, setUserList] = useState<Array<UserDTO>>([]);
  const [addedUser, setAddedUser] = useState<Array<UserRoleDTO>>([]);
  const [userSelection, setUserSelection] = useState<number>(-1);

  const onChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setText(event.target.value as string);
  };

  const addUserInList = () => {
    if (addedUser.findIndex((elm) => elm.id === userSelection) < 0) {
      const index = userList.findIndex((elm) => elm.id === userSelection);
      if (index >= 0) {
        const newUserDTO: UserRoleDTO = {
          id: userSelection,
          name: userList[index].name,
          role: RoleType.READER,
        };
        setAddedUser(addedUser.concat([newUserDTO]));
      }
    }
  };

  const onUpdateRole = (id: number, role: RoleType): void => {
    const tmpList: Array<UserRoleDTO> = ([] as Array<UserRoleDTO>).concat(addedUser);
    const index = tmpList.findIndex((elm) => elm.id === id);
    if (index >= 0) {
      tmpList[index].role = role;
      setAddedUser(tmpList);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        let users: Array<UserDTO> = await getUsers();
        users = users.filter((elm) => elm.name !== 'admin' && elm.id !== userId && (group !== undefined ? group.users.findIndex((item) => item.id === elm.id) < 0 : true));
        setUserList(users);
        if (users.length > 0) {
          setUserSelection(users[0].id);
        }
        setText(group ? group.group.name : '');
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('settings:usersError'), e as AxiosError);
      }
    };
    init();
  }, [enqueueSnackbar, group, t, userId]);

  return (

    <GenericModal
      open={open}
      handleClose={onClose}
      handleAction={() => onSave(text, addedUser)}
      title={group ? `${t('settings:group')} - ${group.group.name}` : t('settings:newGroupTitle')}
    >
      {(isAdmin || group === undefined) && (
      <div className={classes.infos}>
        <TextField
          className={classes.idFields}
          label={t('settings:groupNameLabel')}
          variant="outlined"
          onChange={onChange}
          value={text}
        />
      </div>
      )}
      <div className={classes.addInfo}>
        <div className={classes.userSelect}>
          <Typography variant="h6" component="div" className={classes.addText}>{t('settings:users')}</Typography>
          <Select
            value={userSelection}
            onChange={(event: React.ChangeEvent<{ value: unknown }>) =>
              setUserSelection(event.target.value as number)
          }
            label={t('settings:groupNameLabel')}
            className={classes.select}
          >
            {userList.map((item) => (
              <MenuItem key={item.id} value={item.id}>
                {t(item.name)}
              </MenuItem>
            ))}
          </Select>
        </div>
        <Button variant="contained" color="primary" onClick={addUserInList}>
          {t('settings:addButton')}
        </Button>
      </div>
      <div className={classes.userList}>
        {
            addedUser.map((item) => (
              <div key={item.id} className={classes.user}>
                <Typography style={{ fontWeight: 'bold' }}>{item.name}</Typography>
                <Select
                  value={item.role}
                  onChange={(event: React.ChangeEvent<{ value: unknown }>) =>
                    onUpdateRole(item.id, event.target.value as RoleType)
                  }
                  label={t('settings:groupNameLabel')}
                  className={classes.roleSelect}
                >
                  {menuItems.map((elm) => (
                    <MenuItem key={elm.role} value={elm.role}>
                      {t(elm.tr)}
                    </MenuItem>
                  ))}
                </Select>

              </div>
            ))
          }
      </div>
    </GenericModal>
  );
};

export default GroupModal;
