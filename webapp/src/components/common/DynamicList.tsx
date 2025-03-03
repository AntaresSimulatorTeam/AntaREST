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

import React from "react";
import { Grid, Divider, IconButton } from "@mui/material";
import { t } from "i18next";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";
import SelectFE from "./fieldEditors/SelectFE";

interface ListOption {
  label: string;
  value: string;
}

export interface DynamicListProps<T extends { id: string } = { id: string }> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  options: ListOption[];
  onAdd: (value: string) => void;
  onDelete: (index: number) => void;
  allowEmpty?: boolean;
  disableDelete?: (item: T) => boolean;
}

function DynamicList<T extends { id: string }>({
  items,
  renderItem,
  options,
  onAdd,
  onDelete,
  allowEmpty = true,
  disableDelete,
}: DynamicListProps<T>) {
  return (
    <Grid container direction="column" spacing={2}>
      <Grid item>
        {items.map((item, index) => (
          <React.Fragment key={item.id}>
            <Grid container spacing={1} alignItems="center">
              {renderItem(item, index)}
              <Grid item xs={2} md={1}>
                <IconButton
                  onClick={() => onDelete(index)}
                  disabled={disableDelete?.(item) ?? (items.length === 1 && !allowEmpty)}
                >
                  <RemoveCircleOutlineIcon />
                </IconButton>
              </Grid>
            </Grid>
          </React.Fragment>
        ))}
      </Grid>
      <Grid item>
        <Divider orientation="horizontal" />
      </Grid>
      <Grid item>
        {options.length > 0 && (
          <SelectFE
            label={t("global.area.add")}
            options={options}
            value=""
            onChange={(e) => onAdd(e.target.value as string)}
            variant="outlined"
            sx={{ width: 200, mb: 2 }}
          />
        )}
      </Grid>
    </Grid>
  );
}

export default DynamicList;
