import React from "react";
import { Grid, Divider } from "@mui/material";
import SelectFE from "./fieldEditors/SelectFE";

interface ListOption {
  label: string;
  value: string;
}

interface DynamicListProps<T extends { id: string }> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  options: ListOption[];
  onAdd: (value: string) => void;
}

function DynamicList<T extends { id: string }>({
  items,
  renderItem,
  options,
  onAdd,
}: DynamicListProps<T>) {
  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Grid container direction="column" spacing={2}>
      <Grid item>
        {items.map((item, index) => (
          <React.Fragment key={item.id}>
            {renderItem(item, index)}
          </React.Fragment>
        ))}
      </Grid>
      <Grid item>
        <Divider orientation="horizontal" />
      </Grid>
      <Grid item>
        {options.length > 0 && (
          <SelectFE
            label="Add item"
            options={options}
            onChange={(e) => onAdd(e.target.value as string)}
            size="small"
            variant="outlined"
            sx={{ width: 200 }}
          />
        )}
      </Grid>
    </Grid>
  );
}

export default DynamicList;
