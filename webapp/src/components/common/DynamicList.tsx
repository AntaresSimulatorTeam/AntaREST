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
}

function DynamicList<T extends { id: string }>({
  items,
  renderItem,
  options,
  onAdd,
  onDelete,
  allowEmpty = true,
}: DynamicListProps<T>) {
  const disableDelete = items.length === 1 && !allowEmpty;

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
                  disabled={disableDelete}
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
            onChange={(e) => onAdd(e.target.value as string)}
            size="small"
            variant="outlined"
            sx={{ width: 200, mb: 2 }}
          />
        )}
      </Grid>
    </Grid>
  );
}

export default DynamicList;
