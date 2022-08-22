import {
  Checkbox,
  CheckboxProps,
  FormControl,
  FormControlLabel,
  FormControlLabelProps,
  FormHelperText,
} from "@mui/material";
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
    ...checkboxProps
  } = props;

  const fieldEditor = (
    <Checkbox
      {...checkboxProps}
      checked={value}
      defaultChecked={defaultValue}
    />
  );

  return (
    <FormControl className={className} sx={sx} error={error}>
      {label ? (
        <FormControlLabel
          control={fieldEditor}
          label={label}
          labelPlacement={labelPlacement}
        />
      ) : (
        fieldEditor
      )}
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
}

export default reactHookFormSupport({ defaultValue: false })(CheckBoxFE);
