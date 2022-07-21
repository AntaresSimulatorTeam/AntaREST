import {
  Checkbox,
  CheckboxProps,
  FormControlLabel,
  FormControlLabelProps,
} from "@mui/material";
import clsx from "clsx";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

export interface CheckBoxFEProps
  extends Omit<CheckboxProps, "checked" | "defaultChecked" | "defaultValue"> {
  value?: boolean;
  defaultValue?: boolean;
  label?: string;
  labelPlacement?: FormControlLabelProps["labelPlacement"];
  error?: boolean;
  helperText?: React.ReactNode;
}

function CheckBoxFE(props: CheckBoxFEProps) {
  const {
    value,
    defaultValue,
    label,
    labelPlacement,
    helperText,
    error,
    className,
    sx,
    inputRef,
    ...rest
  } = props;

  const fieldEditor = (
    <Checkbox
      {...rest}
      className={clsx(!label && ["CheckBoxFE", className])}
      sx={!label ? sx : undefined}
      checked={value}
      defaultChecked={defaultValue}
      inputRef={inputRef}
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

export default reactHookFormSupport({ defaultValue: false })(CheckBoxFE);
