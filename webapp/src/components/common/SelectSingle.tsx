import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  SelectProps,
  SxProps,
  Theme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { GenericInfo } from "../../common/types";

interface Props extends SelectProps {
  name: string;
  label?: string;
  list: GenericInfo[];
  data: string | undefined;
  setValue?: (data: string) => void;
  sx?: SxProps<Theme> | undefined;
  optional?: boolean;
  variant?: "filled" | "standard" | "outlined" | undefined;
  handleChange?: (key: string, value: string | number) => void;
  required?: boolean;
  disabled?: boolean;
}

function SelectSingle(props: Props) {
  const {
    name,
    label = name,
    list,
    data,
    setValue,
    sx,
    variant,
    optional,
    handleChange,
    required,
    disabled,
  } = props;
  const [t] = useTranslation();

  const basicHandleChange = (e: SelectChangeEvent<unknown>) => {
    if (setValue) {
      setValue(e.target.value as string);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormControl variant={variant} sx={sx} required={required}>
      <InputLabel id={`single-checkbox-label-${name}`}>{label}</InputLabel>
      <Select
        {...props}
        labelId={`single-checkbox-label-${name}`}
        id={`single-checkbox-${name}`}
        value={data}
        label={label}
        disabled={disabled}
        onChange={
          handleChange
            ? (e: SelectChangeEvent<unknown>) =>
                handleChange(name, e.target.value as string)
            : basicHandleChange
        }
      >
        {optional && (
          <MenuItem key="None" value="">
            {t("global.none")}
          </MenuItem>
        )}
        {list.map(({ id, name }) => (
          <MenuItem key={id} value={id}>
            {t(name)}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

SelectSingle.defaultProps = {
  sx: { m: 0, width: 200 },
  variant: "filled",
  label: undefined,
  optional: false,
  setValue: undefined,
  handleChange: undefined,
  required: false,
};

export default SelectSingle;
