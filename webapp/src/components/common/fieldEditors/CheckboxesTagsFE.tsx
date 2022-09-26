import {
  Autocomplete,
  AutocompleteProps,
  AutocompleteValue,
  Checkbox,
  TextField,
} from "@mui/material";
import CheckBoxOutlineBlankIcon from "@mui/icons-material/CheckBoxOutlineBlank";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import { FieldPath, FieldValues } from "react-hook-form";
import reactHookFormSupport, {
  ReactHookFormSupportProps,
} from "../../../hoc/reactHookFormSupport";

interface CheckboxesTagsFEProps<
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined
> extends Omit<
    AutocompleteProps<T, true, DisableClearable, FreeSolo>,
    | "multiple"
    | "disableCloseOnSelect"
    | "renderOption"
    | "renderInput"
    | "renderTags"
    | "onChange"
  > {
  label?: string;
  error?: boolean;
  helperText?: string;
  inputRef?: React.Ref<unknown>;
  name?: string;
  onChange?: (
    event: React.SyntheticEvent & {
      target: {
        value: AutocompleteValue<T, true, DisableClearable, FreeSolo>;
        name: string | "";
      };
    }
  ) => void;
}

// TODO Add `onChange`'s value in `inputRef` and `onBlur`'s event

function CheckboxesTagsFE<
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined
>(props: CheckboxesTagsFEProps<T, DisableClearable, FreeSolo>) {
  const {
    label,
    // Default value on MUI
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    getOptionLabel = (option: any) => option?.label ?? option,
    error,
    helperText,
    inputRef,
    onChange,
    name = "",
    ...rest
  } = props;

  return (
    <Autocomplete
      {...rest}
      getOptionLabel={getOptionLabel}
      multiple
      disableCloseOnSelect
      onChange={(event, value) => {
        onChange?.({
          ...event,
          target: {
            ...event.target,
            value,
            name,
          },
        });
      }}
      renderOption={(props, option, { selected }) => (
        <li {...props}>
          <Checkbox
            icon={<CheckBoxOutlineBlankIcon fontSize="small" />}
            checkedIcon={<CheckBoxIcon fontSize="small" />}
            style={{ marginRight: 8 }}
            checked={selected}
          />
          {getOptionLabel(option)}
        </li>
      )}
      renderInput={(params) => (
        <TextField
          sx={{ m: 0 }}
          name={name}
          variant="filled"
          label={label}
          error={error}
          helperText={helperText}
          inputRef={inputRef}
          {...params}
        />
      )}
    />
  );
}

// TODO find a clean solution to support generics

export default reactHookFormSupport()(CheckboxesTagsFE) as <
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined,
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any
>(
  props: ReactHookFormSupportProps<TFieldValues, TFieldName, TContext> &
    CheckboxesTagsFEProps<T, DisableClearable, FreeSolo>
) => JSX.Element;
