import {
  FormControlLabel,
  FormControlLabelProps,
  Switch,
  SwitchProps,
} from "@mui/material";
import clsx from "clsx";
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
    className,
    sx,
    ...rest
  } = props;

  const fieldEditor = (
    <Switch
      {...rest}
      className={clsx(!label && ["SwitchFE", className])}
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
        className={clsx("SwitchFE", className)}
        control={fieldEditor}
        label={label}
        labelPlacement={labelPlacement}
      />
    );
  }

  return fieldEditor;
});

SwitchFE.displayName = "SwitchFE";

export default SwitchFE;
