import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles, Theme, Select, MenuItem } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../ui/GenericModal';
import { GroupDTO, RoleType, UserRoleDTO } from '../../../common/types';
import { menuItems } from './utils';

const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing(3),
    marginBottom: theme.spacing(2),
  },
  roleList: {
    width: '100%',
    height: '60px',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    display: 'flex',
    alignItems: 'center',
    margin: theme.spacing(1),
  },
  select: {
    margin: theme.spacing(2),
    maxWidth: '400px',
  },
}));

interface PropTypes {
    open: boolean;
    onClose: () => void;
    onSave: (groupId: string, userId: number, role: RoleType) => void;
    group: GroupDTO | undefined;
    user: UserRoleDTO;
}

const RoleModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, group, user, onClose, onSave } = props;
  const [selection, setSelection] = useState<RoleType>(user !== undefined ? user.role : RoleType.READER);

  useEffect(() => {
    setSelection(user !== undefined ? user.role : RoleType.READER);
  }, [user]);

  return (

    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={() => onSave(group?.id as string, user.id, selection)}
      title={`${user?.name} in "${group?.name}"`}
    >
      <div className={classes.roleList}>
        <Select
          value={selection}
          onChange={(event: React.ChangeEvent<{ value: unknown }>) =>
            setSelection(event.target.value as RoleType)
          }
          label={t('settings:groupNameLabel')}
          className={classes.select}
        >
          {menuItems.map((item) => (
            <MenuItem key={item.role} value={item.role}>
              {t(item.tr)}
            </MenuItem>
          ))}
        </Select>
      </div>
    </GenericModal>
  );
};

export default RoleModal;
