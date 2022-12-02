import {
  FormControl,
  FormControlLabel,
  FormControlLabelProps,
  FormHelperText,
  Radio,
  RadioProps,
} from "@mui/material";

export interface RadioFEProps extends RadioProps {
  label?: string;
  labelPlacement?: FormControlLabelProps["labelPlacement"];
  error?: boolean;
  helperText?: React.ReactNode;
}

function RadioFE(props: RadioFEProps) {
  const {
    value,
    label,
    labelPlacement,
    helperText,
    error,
    className,
    sx,
    ...radioProps
  } = props;

  const fieldEditor = <Radio value={value} {...radioProps} />;

  return (
    <FormControl className={className} sx={sx} error={error}>
      {label ? (
        <FormControlLabel
          control={fieldEditor}
          label={label}
          labelPlacement={labelPlacement}
          value={value} // For RadioGroup
        />
      ) : (
        fieldEditor
      )}
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
}

export default RadioFE;
