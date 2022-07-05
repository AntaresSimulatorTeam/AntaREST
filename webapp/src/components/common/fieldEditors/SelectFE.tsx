import {
  FormControl,
  FormControlProps,
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
import { O } from "ts-toolbelt";

type OptionObj<T extends O.Object = O.Object> = {
  label: string;
  value: string | number;
} & T;

export interface SelectFEProps
  extends Omit<SelectProps, "labelId" | "inputRef"> {
  options: Array<string | OptionObj>;
  helperText?: React.ReactNode;
  emptyValue?: boolean;
  formControlProps?: FormControlProps;
}

function formatOptions(
  options: SelectFEProps["options"]
): Array<OptionObj<{ id: string }>> {
  return options.map((opt) => ({
    ...(RA.isPlainObj(opt) ? opt : { label: startCase(opt), value: opt }),
    id: uuidv4(),
  }));
}

const SelectFE = forwardRef((props: SelectFEProps, ref) => {
  const {
    options,
    helperText,
    emptyValue,
    variant = "filled",
    formControlProps,
    ...selectProps
  } = props;
  const { label } = selectProps;
  const labelId = useRef(uuidv4()).current;

  const optionsFormatted = useMemo(
    () => formatOptions(options),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(options)]
  );

  return (
    <FormControl variant={variant} {...formControlProps}>
      <InputLabel id={labelId}>{label}</InputLabel>
      <Select {...selectProps} labelId={labelId} inputRef={ref}>
        {emptyValue && (
          <MenuItem value="">
            {/* TODO i18n */}
            <em>None</em>
          </MenuItem>
        )}
        {optionsFormatted.map(({ id, value, label }) => (
          <MenuItem key={id} value={value}>
            {label}
          </MenuItem>
        ))}
      </Select>
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
});

SelectFE.displayName = "SelectFE";

export default SelectFE;
