import React, { PropsWithChildren } from 'react';
import { connect, ConnectedProps,  } from 'react-redux';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import { Checkbox, FormControl, InputLabel, ListItemText, MenuItem, OutlinedInput, Select, SelectChangeEvent, useTheme } from '@mui/material';
import { GenericInfo, IDType } from '../common/types';


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

interface Props {
   name: string;
   list: Array<GenericInfo>;
   data: Array<string>;
   setValue: (data: Array<string>) => void;
}

const FilterDrawer = (props: Props) => {
  const theme = useTheme();
  const { name, list, data, setValue } = props;

  const handleChange = (event: SelectChangeEvent<Array<string>>) => {
    const {
      target: { value },
    } = event;
    setValue(typeof value === 'string' ? value.split(',') : value);
  };
  
  return (
    <FormControl sx={{ m: 1, width: 200 }}>
        <InputLabel id="multiple-checkbox-label">{name}</InputLabel>
        <Select
        labelId="multiple-checkbox-label"
        id="multiple-checkbox"
        multiple
        value={data}
        onChange={handleChange}
        input={<OutlinedInput label={name} />}
        renderValue={(selected) => selected.join(', ')}
        MenuProps={MenuProps}
        >
        {list.map(({id, name}) => (
            <MenuItem key={id} value={name}>
                <Checkbox checked={data.indexOf(name) > -1} />
                <ListItemText primary={name} />
            </MenuItem>
        ))}
        </Select>
    </FormControl>
  );
}

export default FilterDrawer;