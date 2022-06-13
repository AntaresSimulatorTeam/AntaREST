import {
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  SelectProps,
} from "@mui/material";
import { forwardRef, useMemo, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import * as RA from "ramda-adjunct";
import { startCase } from "lodash";

type OptionsObj = Array<{ label: string; value: string }>;

interface SelectFEProps extends Omit<SelectProps, "labelId"> {
  options: string[] | OptionsObj;
  helperText?: React.ReactNode;
  emptyValue?: boolean;
}

function formatOptions(options: SelectFEProps["options"]): OptionsObj {
  if (options.length === 0 || RA.isPlainObj(options[0])) {
    return options as OptionsObj;
  }
  return (options as string[]).map((opt) => ({
    label: startCase(opt),
    value: opt,
  }));
}

const SelectFE = forwardRef((props: SelectFEProps, ref) => {
  const { options, helperText, emptyValue, variant, ...selectProps } = props;
  const { label } = selectProps;
  const labelId = useRef(uuidv4()).current;

  const optionsFormatted = useMemo(
    () => formatOptions(options),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(options)]
  );

  return (
    <FormControl variant={variant}>
      <InputLabel id={labelId}>{label}</InputLabel>
      <Select
        variant={variant}
        {...selectProps}
        labelId={labelId}
        inputRef={ref}
      >
        {emptyValue && (
          <MenuItem value="">
            <em>None</em>
          </MenuItem>
        )}
        {optionsFormatted.map(({ value, label }) => (
          <MenuItem key={value} value={value}>
            {label}
          </MenuItem>
        ))}
      </Select>
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
});

export default SelectFE;
