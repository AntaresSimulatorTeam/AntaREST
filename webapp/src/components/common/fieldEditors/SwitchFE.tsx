import {
  FormControl,
  FormControlLabel,
  FormControlLabelProps,
  FormHelperText,
  Switch,
  SwitchProps,
} from "@mui/material";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";
import { mergeSxProp } from "../../../utils/muiUtils";

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
    ...switchProps
  } = props;

  const fieldEditor = (
    <Switch {...switchProps} checked={value} defaultChecked={defaultValue} />
  );

  return (
    <FormControl
      className={className}
      sx={mergeSxProp({ alignSelf: "center" }, sx)}
      error={error}
    >
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

export default reactHookFormSupport({ defaultValue: false })(SwitchFE);
