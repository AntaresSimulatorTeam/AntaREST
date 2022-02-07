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

const SingleSelect = (props: PropTypes) => {
  const { list, label, style, fullWidth, value, onChange } = props;

  return (
    <FormControl fullWidth={fullWidth !== undefined ? fullWidth : false} style={style}>
      <InputLabel id={`single-filter-label-${label}`}>{label}</InputLabel>
      <Select
        labelId={`single-filter-label-${label}`}
        id={`single-filter-${label}`}
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

SingleSelect.defaultProps = {
  style: undefined,
  fullWidth: false,
};

export default SingleSelect;
