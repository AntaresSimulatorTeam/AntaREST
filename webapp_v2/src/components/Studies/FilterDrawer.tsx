import React, { PropsWithChildren, useState } from 'react';
import { connect, ConnectedProps,  } from 'react-redux';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Divider from '@mui/material/Divider';
import { Checkbox, Drawer, FormControl, FormControlLabel, InputLabel, ListItem, ListItemText, MenuItem, OutlinedInput, Select, SelectChangeEvent, Typography, useTheme } from '@mui/material';
import { DRAWER_WIDTH_EXTENDED } from '../../theme';
import SelectMulti from '../SelectMulti';
import { GenericInfo } from '../../common/types';


const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};
  const names = [
    'Oliver Hansen',
    'Van Henry',
    'April Tucker',
    'Ralph Hubbard',
    'Omar Alexander',
    'Carlos Abbott',
    'Miriam Wagner',
    'Bradley Wilkerson',
    'Virginia Andrews',
    'Kelly Snyder',
  ];

interface Props {
    open: boolean;
}

const FilterDrawer = (props: Props) => {
  const theme = useTheme();
  const [t] = useTranslation();
  const { open } = props;
  const [versions, setVersions] = useState<Array<GenericInfo>>([]);
  const versionList: Array<GenericInfo> = [{id: 0, name: '0.1'}, {id: 1, name: '1.0'}, {id: 1, name: '2.0'}];

  const setVersionFilter = (data: string | Array<string>) : void => {
      console.log(data);

  }
  
  return (

      <Drawer
        variant="persistent"
        anchor="right"
        open={open}
        sx={{ 
          width: DRAWER_WIDTH_EXTENDED,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH_EXTENDED,
            boxSizing: 'border-box',
            overflow: 'hidden',
            backgroundColor: theme.palette.primary.dark,
            borderRight: `1px solid ${theme.palette.grey[800]}`,
          },
        }}
      >
        <Toolbar sx={{ py: 3 }}>
          <Box display="flex" width="100%" height="100%" justifyContent='flex-start' alignItems="flex-start" py={2} flexDirection="column" flexWrap="nowrap" boxSizing="border-box" color='white'>
            <Typography sx={{ color: 'grey.500', fontSize: '0.9em', mb: theme.spacing(2) }} >{t('main:filter').toUpperCase()}</Typography>
            <FormControlLabel control={<Checkbox sx={{ color: 'white' }} />} label="Managed studies" />
          </Box>
        </Toolbar>
        <Divider style={{ height: '1px', backgroundColor: theme.palette.grey[800] }}/>
        <List>
            <ListItem>
              {/*<SelectMulti name="Version" list={versionList} data={versions} setValue={setVersionFilter}/>*/}
            </ListItem>
            <ListItem>
                <ListItemText primary="User" />
            </ListItem>
            <ListItem>
                <ListItemText primary="Group" />
            </ListItem>
        </List>
        <Box display="flex" width="100%" height="100%" justifyContent='flex-start' alignItems="center" flexDirection="row" flexWrap="nowrap" boxSizing="border-box">
        </Box>
      </Drawer>
  );
}

export default FilterDrawer;