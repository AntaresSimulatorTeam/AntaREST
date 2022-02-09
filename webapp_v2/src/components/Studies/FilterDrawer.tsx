import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Divider from '@mui/material/Divider';
import { Button, Checkbox, Drawer, FormControlLabel, InputLabel, ListItem, ListItemText, MenuItem, OutlinedInput, Select, SelectChangeEvent, Typography, useTheme } from '@mui/material';
import { STUDIES_FILTER_WIDTH } from '../../theme';
import SelectMulti from '../SelectMulti';
import { GenericInfo, GroupDTO, UserDTO } from '../../common/types';
import { convertVersions } from '../../services/utils';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;

interface Props {
    open: boolean;
    managedFilter: boolean;
    setManagedFilter: (data: boolean) => void;
    versionList: Array<GenericInfo>;
    versions: Array<GenericInfo>;
    userList: Array<UserDTO>;
    users: Array<UserDTO>;
    groupList: Array<GroupDTO>;
    groups: Array<GroupDTO>;
    onFilterActionClick: (versions: Array<GenericInfo> | undefined,
                          users: Array<UserDTO> | undefined,
                          groups: Array<GroupDTO> | undefined) => void;
    onClose: () => void;
}

function FilterDrawer(props: Props) {
  const theme = useTheme();
  const [t] = useTranslation();
  const { open, managedFilter, setManagedFilter, versionList, versions, userList, users, groupList, groups, onFilterActionClick, onClose } = props;

  const [currentUsers, setCurrentUsers] = useState<Array<UserDTO>|undefined>(users);
  const [currentGroups, setCurrentGroups] = useState<Array<GroupDTO>|undefined>(groups);
  const [currentVersions, setCurrentVersions] = useState<Array<GenericInfo> | undefined>(versions);

  const setVersions = (data: Array<string>) : void => {
    setCurrentVersions(convertVersions(data || []));
  };

  const setUsers = (data: Array<string>) : void => {
    setCurrentUsers(data.map((elm) => {
      const index = userList.findIndex((item) => {
        console.log('ID: ', item.id.toString());
        return item.id.toString() === elm;
      });
      console.log('ELM: ', elm);
      console.log('TYPEOF: ', typeof elm);
      console.log('USER LIST: ', userList);
      console.log('INDEX:', index);
      return { id: userList[index].id, name: userList[index].name };
    }));
  };

  const setGroups = (data: Array<string>) : void => {
    setCurrentGroups(data.map((elm) => {
      const index = groupList.findIndex((item) => {
        console.log('GROUP ID: ', item.id);
        return item.id === elm;
      });
      console.log('ELM: ', elm);
      console.log('TYPEOF: ', typeof elm);
      console.log('USER LIST: ', groupList);
      console.log('INDEX:', index);
      return { id: groupList[index].id, name: groupList[index].name };
    }));
  };

  const onFilterClick = (): void => {
    onFilterActionClick(currentVersions, currentUsers, currentGroups);
  };

  const onResetFilterClick = (): void => {
    setCurrentVersions(undefined);
    setCurrentUsers(undefined);
    setCurrentGroups(undefined);
  };

  console.log('MANAGED FILTER: ', managedFilter);

  return (

    <Drawer
      variant="temporary"
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        width: STUDIES_FILTER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: STUDIES_FILTER_WIDTH,
          boxSizing: 'border-box',
          overflow: 'hidden',
        },
      }}
    >
      <Toolbar sx={{ py: 3 }}>
        <Box display="flex" width="100%" height="100%" justifyContent="flex-start" alignItems="flex-start" py={2} flexDirection="column" flexWrap="nowrap" boxSizing="border-box" color="white">
          <Typography sx={{ color: 'grey.500', fontSize: '0.9em', mb: theme.spacing(2) }}>{t('main:filter').toUpperCase()}</Typography>
          <FormControlLabel control={<Checkbox checked={managedFilter} onChange={() => setManagedFilter(!managedFilter)} sx={{ color: 'white' }} />} label="Managed studies" />
        </Box>
      </Toolbar>
      <Divider style={{ height: '1px', backgroundColor: theme.palette.grey[800] }} />
      <List>
        <ListItem>
          <SelectMulti name="Version" list={versionList} data={currentVersions !== undefined ? currentVersions.map((elm) => elm.id as string) : []} setValue={setVersions} />
        </ListItem>
        <ListItem>
          <SelectMulti name="Users" list={userList.map((elm) => ({ id: elm.id.toString(), name: elm.name }))} data={currentUsers !== undefined ? currentUsers.map((elm) => elm.id.toString()) : []} setValue={setUsers} />
        </ListItem>
        <ListItem>
          <SelectMulti name="Groups" list={groupList.map((elm) => ({ id: elm.id, name: elm.name }))} data={currentGroups !== undefined ? currentGroups.map((elm) => elm.id) : []} setValue={setGroups} />
        </ListItem>
      </List>
      <Box display="flex" width="100%" flexGrow={1} justifyContent="flex-end" alignItems="center" flexDirection="column" flexWrap="nowrap" boxSizing="border-box">
        <Box display="flex" width="100%" height="auto" justifyContent="flex-end" alignItems="center" flexDirection="row" flexWrap="nowrap" boxSizing="border-box" p={1}>
          <Button variant="text" color="primary" onClick={onResetFilterClick}>
            {t('main:reset')}
          </Button>
          <Button sx={{ mx: 2 }} color="success" variant="contained" onClick={onFilterClick}>
            {t('main:filter')}
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
}

export default FilterDrawer;
