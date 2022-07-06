import { useState } from "react";
import { Chip, ListItem, TextField } from "@mui/material";
import { AddIcon, InputContainer, Root, TagContainer } from "./style";

interface PropTypes {
  label: string;
  values: Array<string>;
  onChange: (value: Array<string>) => void;
}

function TagSelect(props: PropTypes) {
  const { label, values, onChange } = props;
  const [value, setValue] = useState<string>("");

  const onAddTag = (): void => {
    if (values.findIndex((elm) => elm === value) < 0 && value !== "") {
      onChange(values.concat(value));
      setValue("");
    }
  };

  return (
    <Root>
      <InputContainer>
        <TextField
          label={label}
          value={value}
          variant="filled"
          onChange={(event) => setValue(event.target.value)}
          sx={{ m: 0, mr: 1, flex: 1 }}
        />
        <AddIcon onClick={onAddTag} />
      </InputContainer>
      <TagContainer>
        {values.map((elm) => (
          <ListItem key={elm} sx={{ width: "auto" }}>
            <Chip
              label={elm}
              onDelete={() => onChange(values.filter((item) => item !== elm))}
              sx={{ m: 0.5 }}
            />
          </ListItem>
        ))}
      </TagContainer>
    </Root>
  );
}

export default TagSelect;
