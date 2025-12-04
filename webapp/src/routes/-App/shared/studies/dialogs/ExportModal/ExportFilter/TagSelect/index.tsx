/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { useState } from "react";
import { Chip, ListItem, TextField } from "@mui/material";
import { AddIcon, InputContainer, Root, TagContainer } from "./style";

interface PropTypes {
  label: string;
  values: string[];
  onChange: (value: string[]) => void;
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
