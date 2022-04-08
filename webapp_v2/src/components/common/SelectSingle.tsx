import {
  FormControl,
  InputLabel,
  ListItemText,
  MenuItem,
  Select,
  SelectChangeEvent,
  SxProps,
  Theme,
} from "@mui/material";
import { GenericInfo } from "../../common/types";

interface Props {
  name: string;
  list: Array<GenericInfo>;
  data: string | undefined;
  setValue: (data: string) => void;
  sx?: SxProps<Theme> | undefined;
  placeholder?: string;
}

function SelectSingle(props: Props) {
  const { name, list, data, setValue, placeholder, sx } = props;

  const handleChange = (event: SelectChangeEvent<string>) => {
    const {
      target: { value },
    } = event;
    setValue(value);
  };

  return (
    <FormControl sx={sx}>
      <InputLabel
        id={`single-checkbox-label-${name}`}
        sx={{ color: "rgba(255, 255, 255, 0.7)" }}
      >
        {name}
      </InputLabel>
      <Select
        labelId={`single-checkbox-label-${name}`}
        id={`single-checkbox-${name}`}
        value={data}
        variant="filled"
        placeholder={placeholder}
        onChange={handleChange}
        sx={{
          minHeight: 0,
          background: "rgba(255, 255, 255, 0.09)",
          borderRadius: "4px 4px 0px 0px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
          ".MuiSelect-icon": {
            backgroundColor: "#222333",
          },
        }}
      >
        {list.map(({ id, name }) => (
          <MenuItem key={id} value={id}>
            <ListItemText primary={name} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

SelectSingle.defaultProps = {
  sx: { m: 0, width: 200 },
  placeholder: undefined,
};

export default SelectSingle;
