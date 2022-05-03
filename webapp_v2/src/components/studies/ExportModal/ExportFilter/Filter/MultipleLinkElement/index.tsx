import { Chip, ListItem } from "@mui/material";
import { useState } from "react";
import { AddIcon } from "../../TagSelect/style";
import SingleLinkElement from "../SingleLinkElement";
import { LinkContainer } from "../style";
import { FilterLinkContainer, Root } from "./style";

export default function MultipleLinkElement(props: {
  label: string;
  areas: Array<string>;
  values: Array<string>;
  onChange: (value: Array<string>) => void;
}) {
  const { label, areas, values, onChange } = props;
  const [currentLink, setCurrentLink] = useState<string>("");

  const onAddLink = (): void => {
    if (
      values.findIndex((elm) => elm === currentLink) < 0 &&
      currentLink !== ""
    ) {
      onChange(values.concat(currentLink));
    }
  };

  return (
    <Root bgcolor="green">
      <LinkContainer multiple>
        <SingleLinkElement
          globalFilter
          label={label}
          areas={areas}
          onChange={setCurrentLink}
        />
        <AddIcon sx={{ bgcolor: "blue" }} onClick={onAddLink} />
      </LinkContainer>
      {values.length > 0 && (
        <FilterLinkContainer>
          {values.map((elm) => (
            <ListItem key={elm}>
              <Chip
                label={elm}
                onDelete={() => onChange(values.filter((link) => link !== elm))}
                sx={{ m: 0.5 }}
              />
            </ListItem>
          ))}
        </FilterLinkContainer>
      )}
    </Root>
  );
}
