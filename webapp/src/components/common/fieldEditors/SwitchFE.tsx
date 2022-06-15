import {
  FormControlLabel,
  FormControlLabelProps,
  Switch,
  SwitchProps,
} from "@mui/material";
import { forwardRef } from "react";

export interface SwitchFEProps
  extends Omit<
    SwitchProps,
    "checked" | "defaultChecked" | "defaultValue" | "inputRef"
  > {
  value?: boolean;
  defaultValue?: boolean;
  label?: string;
  labelPlacement?: FormControlLabelProps["labelPlacement"];
  error?: boolean;
  helperText?: React.ReactNode;
}

const SwitchFE = forwardRef((props: SwitchFEProps, ref) => {
  const {
    value,
    defaultValue,
    label,
    labelPlacement,
    helperText,
    error,
    sx,
    ...rest
  } = props;

  const fieldEditor = (
    <Switch
      {...rest}
      sx={!label ? sx : undefined}
      checked={value}
      defaultChecked={defaultValue}
      inputRef={ref}
    />
  );

  if (label) {
    return (
      <FormControlLabel
        sx={sx}
        control={fieldEditor}
        label={label}
        labelPlacement={labelPlacement}
      />
    );
  }

  return fieldEditor;
});

export default SwitchFE;
