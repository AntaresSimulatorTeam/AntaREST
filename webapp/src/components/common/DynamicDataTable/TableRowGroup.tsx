import {
  TableRow,
  TableCell,
  IconButton,
  Box,
  Typography,
} from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { ChangeEvent, useMemo, useState } from "react";
import TableRowItem from "./TableRowItem";
import { Item, Column, calculateColumnResults } from "./utils";

interface Props {
  itemsByGroup: { group?: string; items: Item[] };
  columns: Column[];
  selected: string[];
  onClick: (e: ChangeEvent<HTMLInputElement>, id: string) => void;
}

function TableRowGroup({
  itemsByGroup: { group, items },
  columns,
  selected,
  onClick,
}: Props) {
  const [openRow, setOpenRow] = useState(false);
  const columnResults = useMemo(
    () => calculateColumnResults(columns, items),
    [columns, items]
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {group && (
        <TableRow
          sx={{
            borderBottom: "2px solid rgba(224, 224, 224, 0.3)",
          }}
        >
          {/* Merge the first two columns into one. The first column, which is always "name",
           * does not contain an operation so no value will be displayed on the TableRowGroup header. */}
          <TableCell colSpan={2} sx={{ py: 0 }}>
            <Box sx={{ display: "flex", alignItems: "center", my: 1 }}>
              <IconButton size="small" onClick={() => setOpenRow(!openRow)}>
                {openRow ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
              </IconButton>
              <Typography sx={{ ml: 2 }}>{group}</Typography>
            </Box>
          </TableCell>
          {/* Skip the first column since it's already included in the merged TableCell above. */}
          {columns.slice(1).map((column) => (
            <TableCell key={column.name} align="center">
              {column.operation && (
                <Typography
                  variant="body2"
                  sx={{
                    color: "rgba(255, 255, 255, 0.5)",
                  }}
                >
                  {columnResults[column.name]}
                </Typography>
              )}
            </TableCell>
          ))}
        </TableRow>
      )}
      {openRow &&
        items.map((item) => (
          <TableRowItem
            key={item.id}
            item={item}
            columns={columns}
            selected={selected}
            onClick={onClick}
          />
        ))}
    </>
  );
}

export default TableRowGroup;
