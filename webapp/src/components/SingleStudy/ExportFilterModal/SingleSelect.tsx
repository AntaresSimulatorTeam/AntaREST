/* eslint-disable @typescript-eslint/camelcase */
import React from 'react';
import { Select, MenuItem, InputLabel, FormControl, Input } from '@material-ui/core';
import { CSSProperties } from '@material-ui/core/styles/withStyles';

interface PropTypes {
    style?: CSSProperties;
    fullWidth?: boolean;
    list: Array<string>;
    value: string;
    label: string;
    onChange: (value: string) => void;
}

const MultipleSelect = (props: PropTypes) => {
  const { list, label, style, fullWidth, value, onChange } = props;

  return (
    <FormControl fullWidth={fullWidth !== undefined ? fullWidth : false} style={style}>
      <InputLabel id="single-filter-label">{label}</InputLabel>
      <Select
        labelId="single-filter-label"
        id="single-filter"
        value={value}
        onChange={(event) => onChange(event.target.value as string)}
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

MultipleSelect.defaultProps = {
  style: undefined,
  fullWidth: false,
};

export default MultipleSelect;
