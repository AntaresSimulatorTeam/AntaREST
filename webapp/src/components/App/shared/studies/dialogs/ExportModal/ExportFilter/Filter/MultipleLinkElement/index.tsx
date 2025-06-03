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

import { Box, Chip, ListItem } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import SelectSingle from "../../../../../../../../common/SelectSingle";
import TextSeparator from "../../../../../../../../common/TextSeparator";
import { AddIcon } from "../../TagSelect/style";
import { Container, FilterLinkContainer, Root } from "./style";

interface FilterLink {
  area1: string;
  area2: string;
}

export default function MultipleLinkElement(props: {
  label: string;
  areas: string[];
  values: string[];
  onChange: (value: string[]) => void;
}) {
  const { label, areas, values, onChange } = props;
  const [t] = useTranslation();
  const [currentLink, setCurrentLink] = useState<string>("");
  const [link, setLink] = useState<FilterLink>({ area1: "", area2: "" });

  const onAddLink = (): void => {
    if (values.findIndex((elm) => elm === currentLink) < 0 && currentLink !== "") {
      onChange(values.concat(currentLink));
    }
  };

  const onSelectChange = (id: number, elm: string): void => {
    let { area1, area2 } = link;
    if (id === 0) {
      area1 = elm;
      setLink({ ...link, area1: elm });
    } else {
      area2 = elm;
      setLink({ ...link, area2: elm });
    }
    setCurrentLink(`${area1}^${area2}`);
  };

  return (
    <Root>
      <Container>
        <TextSeparator text={label} />
        <Box display="flex" width="100%" alignItems="center">
          <SelectSingle
            name={t("study.area1")}
            list={areas.map((elm) => ({ id: elm, name: elm }))}
            data={link.area1}
            setValue={(elm: string[] | string) => onSelectChange(0, elm as string)}
            sx={{ flexGrow: 1, px: 0.5 }}
            required
          />
          <SelectSingle
            name={t("study.area2")}
            list={areas.map((elm) => ({ id: elm, name: elm }))}
            data={link.area2}
            setValue={(elm: string[] | string) => onSelectChange(1, elm as string)}
            sx={{ flexGrow: 1, px: 0.1 }}
            required
          />
          <AddIcon onClick={onAddLink} />
        </Box>
      </Container>
      {values.length > 0 && (
        <FilterLinkContainer>
          {values.map((elm) => (
            <ListItem key={elm} sx={{ width: "auto" }}>
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
