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

import { Box, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import TextSeparator from "../../../../../../common/TextSeparator";
import { Root } from "./style";

interface FilterLink {
  area1: string;
  area2: string;
}

export default function SingleLinkElement(props: {
  label: string;
  onChange: (value: string) => void;
}) {
  const [t] = useTranslation();
  const { label, onChange } = props;
  const [link, setLink] = useState<FilterLink>({ area1: "", area2: "" });

  const onSelectChange = (id: number, elm: string): void => {
    let { area1, area2 } = link;
    if (id === 0) {
      area1 = elm;
      setLink({ ...link, area1: elm });
    } else {
      area2 = elm;
      setLink({ ...link, area2: elm });
    }
    onChange(`${area1}^${area2}`);
  };
  return (
    <Root>
      <TextSeparator text={label} />
      <Box display="flex" flex={1}>
        <TextField
          label={`${t("study.area1")}`}
          value={link.area1}
          onChange={(event) => onSelectChange(0, event.target.value)}
        />
        <TextField
          label={`${t("study.area2")}`}
          value={link.area2}
          onChange={(event) => onSelectChange(1, event.target.value)}
        />
      </Box>
    </Root>
  );
}
