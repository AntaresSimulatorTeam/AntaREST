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

import {
  Box,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
  type SxProps,
  type Theme,
} from "@mui/material";
import ArrowRightOutlinedIcon from "@mui/icons-material/ArrowRightOutlined";
import type { IdType } from "../../../../../types/types";
import { mergeSxProp } from "../../../../../utils/muiUtils";

interface Props<T> {
  list: T[];
  currentElement?: string;
  currentElementKeyToTest?: keyof T;
  setSelectedItem: (item: T, index: number) => void;
  sx?: SxProps<Theme>;
}

function ListElement<T extends { id?: IdType; name: string; label?: string }>({
  list,
  currentElement,
  currentElementKeyToTest,
  setSelectedItem,
  sx,
}: Props<T>) {
  return (
    <Box width="100%" flexGrow={1} flexShrink={1} sx={mergeSxProp({ overflow: "auto", py: 1 }, sx)}>
      {list.map((element, index) => (
        <ListItemButton
          selected={currentElement === element[currentElementKeyToTest || "name"]}
          onClick={() => setSelectedItem(element, index)}
          key={element.id || element.name}
          sx={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            py: 0,
          }}
        >
          <Tooltip title={element.name} placement="right">
            <ListItemText
              sx={{
                "&> span": {
                  textOverflow: "ellipsis",
                  overflow: "hidden",
                  whiteSpace: "nowrap",
                },
              }}
            >
              {element.label || element.name}
            </ListItemText>
          </Tooltip>
          <ListItemIcon
            sx={{
              minWidth: 0,
              width: "auto",
              p: 0,
              display: "flex",
            }}
          >
            <ArrowRightOutlinedIcon color="primary" />
          </ListItemIcon>
        </ListItemButton>
      ))}
    </Box>
  );
}

export default ListElement;
