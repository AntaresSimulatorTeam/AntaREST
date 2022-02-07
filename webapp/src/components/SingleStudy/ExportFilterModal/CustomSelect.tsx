/* eslint-disable @typescript-eslint/camelcase */
import React from 'react';
import { Select, MenuItem, InputLabel, FormControl, Input } from '@material-ui/core';
import { CSSProperties } from '@material-ui/core/styles/withStyles';

interface PropTypes {
    style?: CSSProperties;
    fullWidth?: boolean;
    list: Array<string>;
    value: Array<string> | string;
    label: string;
    multiple?: boolean;
    onChange: (value: Array<string> | string) => void;
}

const CustomSelect = (props: PropTypes) => {
  const { list, label, style, fullWidth, value, multiple, onChange } = props;

  return (
    <FormControl fullWidth={fullWidth !== undefined ? fullWidth : false} style={style}>
      <InputLabel id={`filter-label-${label}`}>{label}</InputLabel>
      <Select
        labelId={`filter-label-${label}`}
        id={`filter-${label}`}
        multiple={multiple}
        value={multiple === true ? value as Array<string> : value as string}
        onChange={(event) => onChange(multiple === true ? event.target.value as Array<string> : event.target.value as string)}
        input={<Input />}
      >
        {list.map((elm) => (
          <MenuItem key={elm} value={elm}>
            {elm}
          </MenuItem>
        ))}
      </Select>
    </FormControl>

  );
};

CustomSelect.defaultProps = {
  style: undefined,
  fullWidth: false,
  multiple: undefined,
};

export default CustomSelect;
