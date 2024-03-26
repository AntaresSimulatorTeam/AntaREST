import { Chip } from "@mui/material";
import type { MRT_Cell, MRT_RowData } from "material-react-table";
import { useTranslation } from "react-i18next";

interface Props<T extends MRT_RowData> {
  cell: MRT_Cell<T, boolean>;
}

function BooleanCell<T extends MRT_RowData>({ cell }: Props<T>) {
  const { t } = useTranslation();

  return (
    <Chip
      label={cell.getValue() ? t("button.yes") : t("button.no")}
      color={cell.getValue() ? "success" : "error"}
      size="small"
      sx={{ minWidth: 40 }}
    />
  );
}

export default BooleanCell;
