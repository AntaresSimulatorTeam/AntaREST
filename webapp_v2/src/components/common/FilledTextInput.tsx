import * as React from "react";
import {
  TextField,
  SxProps,
  Theme,
  InputBaseComponentProps,
} from "@mui/material";

interface Props {
  label: string;
  value?: string;
  fullWidth?: boolean;
  type?: React.HTMLInputTypeAttribute | undefined;
  onChange?: (value: string) => void;
  sx?: SxProps<Theme> | undefined;
  inputProps?: InputBaseComponentProps | undefined;
}
function FilledTextInput(props: Props) {
  const { label, fullWidth, value, onChange, sx, inputProps, type } = props;
  return (
    <TextField
      label={label}
      value={value}
      fullWidth={fullWidth}
      type={type}
      onChange={
        onChange !== undefined
          ? (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) =>
              onChange(e.target.value as string)
          : onChange
      }
      variant="filled"
      inputProps={inputProps}
      sx={{
        ...sx,
        background: "rgba(255, 255, 255, 0.09)",
        borderRadius: "4px 4px 0px 0px",
        borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
      }}
    />
  );
}

FilledTextInput.defaultProps = {
  sx: undefined,
  inputProps: undefined,
  onChange: undefined,
  value: undefined,
  fullWidth: undefined,
  type: undefined,
};

export default FilledTextInput;
