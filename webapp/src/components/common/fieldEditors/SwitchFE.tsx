import {
  FormControlLabel,
  FormControlLabelProps,
  Switch,
  SwitchProps,
} from "@mui/material";
import clsx from "clsx";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

export interface SwitchFEProps
  extends Omit<SwitchProps, "checked" | "defaultChecked" | "defaultValue"> {
  value?: boolean;
  defaultValue?: boolean;
  label?: string;
  labelPlacement?: FormControlLabelProps["labelPlacement"];
  error?: boolean;
  helperText?: React.ReactNode;
}

function SwitchFE(props: SwitchFEProps) {
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
}

export default reactHookFormSupport({ defaultValue: false })(SwitchFE);
