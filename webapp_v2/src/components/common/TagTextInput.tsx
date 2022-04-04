/* eslint-disable react/jsx-props-no-spreading */
/* eslint-disable no-use-before-define */
import React from "react";
import Chip from "@mui/material/Chip";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { SxProps, Theme } from "@mui/material";

interface Props {
  label: string;
  value: Array<string>;
  fullWidth?: boolean;
  type?: React.HTMLInputTypeAttribute | undefined;
  onChange: (values: Array<string>) => void;
  sx?: SxProps<Theme> | undefined;
  tagList: Array<string>;
}

function TagTextInput(props: Props) {
  const { label, fullWidth, sx, type, value, tagList, onChange } = props;
  return (
    <Autocomplete
      multiple
      id="tags-filled"
      value={value}
      options={tagList}
      freeSolo
      fullWidth={fullWidth}
      onChange={(e, value, r) => onChange(value)}
      sx={{
        ...sx,
        background: "rgba(255, 255, 255, 0.09)",
        borderRadius: "4px 4px 0px 0px",
        borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
      }}
      renderTags={(value: readonly string[], getTagProps) =>
        value.map((option: string, index: number) => (
          <Chip variant="outlined" label={option} {...getTagProps({ index })} />
        ))
      }
      renderInput={(params) => (
        <TextField
          {...params}
          variant="filled"
          placeholder={label}
          type={type}
        />
      )}
    />
  );
}

TagTextInput.defaultProps = {
  sx: undefined,
  fullWidth: undefined,
  type: undefined,
};

export default TagTextInput;
