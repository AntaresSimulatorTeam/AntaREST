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

import { TableCell, Checkbox, Chip, TableRow } from "@mui/material";
import { memo, useCallback } from "react";
import type { Item, Column } from "./utils";

interface Props {
  item: Item;
  columns: Column[];
  selected: string[];
  onClick: (e: React.ChangeEvent<HTMLInputElement>, name: string) => void;
}

const TableRowItem = memo(function TableRowItem({ item, columns, selected, onClick }: Props) {
  const isSelected = selected.includes(item.id);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onClick(e, item.id);
    },
    [item.id, onClick],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableRow sx={{ "& > *": { borderBottom: "none !important" } }} selected={isSelected}>
      <TableCell padding="none">
        <Checkbox color="primary" checked={isSelected} onChange={handleChange} />
      </TableCell>
      {columns.map((column) => {
        const cellValue = item.columns[column.name];
        return (
          <TableCell
            key={column.name}
            sx={{ py: 0 }}
            align={typeof cellValue === "number" ? "center" : "left"}
          >
            {column.chipColorMap && typeof cellValue === "string" ? (
              <Chip label={cellValue} color={column.chipColorMap[cellValue]} />
            ) : (
              cellValue
            )}
          </TableCell>
        );
      })}
    </TableRow>
  );
});

export default TableRowItem;
