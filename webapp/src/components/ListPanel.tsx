/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { isSearchMatching } from "@/utils/stringUtils";
import AddIcon from "@mui/icons-material/Add";
import {
  Button,
  CircularProgress,
  List,
  ListItem,
  Stack,
  Tooltip,
  type ListItemProps,
} from "@mui/material";
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import SearchFE from "./fieldEditors/SearchFE";
import SearchMultipleFE from "./fieldEditors/SearchMultipleFE";

export interface ListPanelItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  loading?: boolean;
}

export interface ListPanelProps<TItem extends ListPanelItem = ListPanelItem> {
  list: TItem[];
  onAdd?: VoidFunction;
  actions?: React.ReactNode;
  disableSearch?: boolean;
  multipleSearch?: boolean;
  slotProps?: {
    listItem?: Omit<ListItemProps, "children">;
  };
  /**
   * Custom renderer for each list item's content (rendered inside MUI's ListItem)
   */
  renderItem: (item: TItem) => React.ReactNode;
}

function ListPanel<TItem extends ListPanelItem>({
  list,
  onAdd,
  actions,
  renderItem,
  disableSearch = false,
  multipleSearch = false,
  slotProps,
}: ListPanelProps<TItem>) {
  const [searchValues, setSearchValues] = useState<string[]>([]);
  const { t } = useTranslation();
  const hasActions = !!onAdd || !!actions;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getFilteredList = () => {
    if (disableSearch || searchValues.length === 0) {
      return list;
    }
    return list.filter((item) => isSearchMatching(searchValues, item.label));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Stack direction="column">
      {hasActions && (
        <Stack
          gap={1}
          sx={{
            p: 1,
            pb: 0,
          }}
        >
          {onAdd && (
            <Button startIcon={<AddIcon />} variant="contained" onClick={onAdd}>
              {t("global.add")}
            </Button>
          )}
          {actions}
        </Stack>
      )}
      {!disableSearch &&
        list.length > 0 &&
        (multipleSearch ? (
          <SearchMultipleFE
            value={searchValues}
            onSearchValuesChange={setSearchValues}
            size="extra-small"
            fullWidth
            sx={{ p: 1, pb: 0 }}
          />
        ) : (
          <SearchFE
            value={searchValues[0] || ""}
            onSearchValueChange={(value) => setSearchValues(value ? [value] : [])}
            size="extra-small"
            fullWidth
            sx={{ p: 1, pb: 0 }}
          />
        ))}
      <List dense sx={{ overflow: "auto" }}>
        {getFilteredList().map((item) => (
          <Tooltip key={item.id} title={item.label} placement="right">
            <ListItem
              disablePadding
              secondaryAction={
                item.loading && (
                  <CircularProgress color="inherit" size={16} sx={{ verticalAlign: "middle" }} />
                )
              }
              {...slotProps?.listItem}
            >
              {renderItem(item)}
            </ListItem>
          </Tooltip>
        ))}
      </List>
    </Stack>
  );
}

export default ListPanel;
