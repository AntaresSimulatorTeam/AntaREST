import {
  Autocomplete,
  AutocompleteProps,
  Checkbox,
  TextField,
} from "@mui/material";
import CheckBoxOutlineBlankIcon from "@mui/icons-material/CheckBoxOutlineBlank";
import CheckBoxIcon from "@mui/icons-material/CheckBox";

interface CheckboxesTagsProps<
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined
> extends Omit<
    AutocompleteProps<T, true, DisableClearable, FreeSolo>,
    "multiple" | "disableCloseOnSelect" | "renderOption" | "renderInput"
  > {
  label?: string;
}

function CheckboxesTags<
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined
>(props: CheckboxesTagsProps<T, DisableClearable, FreeSolo>) {
  const { label, getOptionLabel, sx, ...rest } = props;

  return (
    <Autocomplete
      {...rest}
      sx={[{ width: 1, p: "8px" }, ...(Array.isArray(sx) ? sx : [sx])]}
      getOptionLabel={getOptionLabel}
      multiple
      disableCloseOnSelect
      renderOption={(props, option, { selected }) => (
        <li {...props}>
          <Checkbox
            icon={<CheckBoxOutlineBlankIcon fontSize="small" />}
            checkedIcon={<CheckBoxIcon fontSize="small" />}
            style={{ marginRight: 8 }}
            checked={selected}
          />
          {getOptionLabel?.(option) ?? String(option)}
        </li>
      )}
      renderInput={(params) => (
        <TextField sx={{ m: 0 }} label={label} {...params} />
      )}
    />
  );
}

CheckboxesTags.defaultProps = {
  label: undefined,
};

export default CheckboxesTags;
