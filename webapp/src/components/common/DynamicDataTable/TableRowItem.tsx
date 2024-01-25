import { TableCell, Checkbox, Chip, TableRow } from "@mui/material";
import { ChangeEvent, memo, useCallback } from "react";
import { Item, Column } from "./utils";

interface Props {
  item: Item;
  columns: Column[];
  selected: string[];
  onClick: (e: ChangeEvent<HTMLInputElement>, name: string) => void;
}

const TableRowItem = memo(function TableRowItem({
  item,
  columns,
  selected,
  onClick,
}: Props) {
  const isSelected = selected.includes(item.id);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      onClick(e, item.id);
    },
    [item.id, onClick],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableRow
      sx={{ "& > *": { borderBottom: "none !important" } }}
      selected={isSelected}
    >
      <TableCell padding="none">
        <Checkbox
          color="primary"
          checked={isSelected}
          onChange={handleChange}
        />
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
              <Chip
                label={cellValue}
                size="small"
                color={column.chipColorMap[cellValue]}
              />
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
