import React from 'react';
import { Box, Checkbox, Chip, FormControl, InputLabel, ListItemText, MenuItem, Select, SelectChangeEvent, SxProps, Theme } from '@mui/material';
import { GenericInfo } from '../../common/types';

interface Props {
   name: string;
   list: Array<GenericInfo>;
   data: Array<string>;
   setValue: (data: Array<string>) => void;
   sx?: SxProps<Theme> | undefined;
   placeholder?: string;
   tagsMode?: boolean;
}

function SelectMulti(props: Props) {
  const { name, list, data, setValue, placeholder, tagsMode, sx } = props;

  const handleChange = (event: SelectChangeEvent<Array<string>>) => {
    const {
      target: { value },
    } = event;
    setValue(typeof value === 'string' ? value.split(',') : value);
  };

  const chipRender = (selected: Array<string>) : React.ReactNode =>
    (
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {selected.map((value) => {
          const element = list.find((item) => (typeof item.id === 'string' ? item.id === value : item.id.toString() === value));
          if (element) { return <Chip key={element.id} label={element.name} />; }
          return undefined;
        })
        }
      </Box>
    );

  const checkboxRender = (selected: Array<string>) : string =>
    selected.map((elm) => (
      list.find((item) => (typeof item.id === 'string' ? item.id === elm : item.id.toString() === elm))?.name
    )).join(', ');

  return (
    <FormControl sx={sx}>
      <InputLabel id="multiple-checkbox-label" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>{name}</InputLabel>
      <Select
        labelId={`multiple-checkbox-label-${name}`}
        id={`multiple-checkbox-${name}`}
        multiple
        value={data}
        variant="filled"
        placeholder={placeholder}
        onChange={handleChange}
        renderValue={tagsMode === true ? chipRender : checkboxRender}
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

SelectMulti.defaultProps = {
  sx: { m: 1, width: 200 },
  placeholder: undefined,
  tagsMode: undefined,
};

export default SelectMulti;
