import React from 'react';
import { Checkbox, FormControl, InputLabel, ListItemText, MenuItem, Select, SelectChangeEvent } from '@mui/material';
import { GenericInfo } from '../common/types';

interface Props {
   name: string;
   list: Array<GenericInfo>;
   data: Array<string>;
   setValue: (data: Array<string>) => void;
}

function SelectMulti(props: Props) {
  const { name, list, data, setValue } = props;

  const handleChange = (event: SelectChangeEvent<Array<string>>) => {
    const {
      target: { value },
    } = event;
    setValue(typeof value === 'string' ? value.split(',') : value);
  };

  return (
    <FormControl sx={{ m: 1, width: 200 }}>
      <InputLabel id="multiple-checkbox-label" sx={{ color: 'white' }}>{name}</InputLabel>
      <Select
        labelId={`multiple-checkbox-label-${name}`}
        id={`multiple-checkbox-${name}`}
        multiple
        value={data}
        variant="filled"
        onChange={handleChange}
        renderValue={(selected) => selected.map((elm) => (
          list.find((item) => (typeof item.id === 'string' ? item.id === elm : item.id.toString() === elm))?.name
        )).join(', ')}
        sx={{
          background: 'rgba(255, 255, 255, 0.09)',
          borderRadius: '4px 4px 0px 0px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.42)',
          '.MuiSelect-icon': {
            backgroundColor: '#222333',
          },
        }}
      >
        {list.map(({ id, name }) => (
          <MenuItem key={id} value={id}>
            <Checkbox checked={data.indexOf(id as string) > -1} />
            <ListItemText primary={name} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export default SelectMulti;
