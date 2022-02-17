import React from 'react';
import { FormControl, InputLabel, ListItemText, MenuItem, Select, SelectChangeEvent } from '@mui/material';
import { GenericInfo } from '../../common/types';

interface Props {
   name: string;
   list: Array<GenericInfo>;
   data: string;
   setValue: (data: string) => void;
}

function SelectSingle(props: Props) {
  const { name, list, data, setValue } = props;

  const handleChange = (event: SelectChangeEvent<string>) => {
    const {
      target: { value },
    } = event;
    setValue(value);
  };

  return (
    <FormControl sx={{ m: 0, width: 200}}>
      <Select
        labelId={`single-checkbox-label-${name}`}
        id={`single-checkbox-${name}`}
        value={data}
        variant="filled"
        onChange={handleChange}
        sx={{
          height: '35px', 
          background: 'rgba(255, 255, 255, 0)',
          borderRadius: '4px 4px 0px 0px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.42)',
          '.MuiSelect-icon': {
            backgroundColor: '#222333',
          },
        }}
      >
        {list.map(({ id, name }) => (
          <MenuItem key={id} value={id}>
            <ListItemText primary={name} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export default SelectSingle;