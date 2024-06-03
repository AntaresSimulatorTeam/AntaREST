import { ReactNode } from "react";
import { Box, Button, SxProps, Theme } from "@mui/material";
import SearchFE from "./fieldEditors/SearchFE";
import { mergeSxProp } from "../../utils/muiUtils";
import { Add } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

interface PropsType {
  topContent?: ReactNode;
  mainContent: ReactNode | undefined;
  secondaryContent?: ReactNode;
  onSearchFilterChange?: (value: string) => void;
  onAdd?: () => void;
  addButtonText?: string;
  sx?: SxProps<Theme>;
}

function PropertiesView({
  onAdd,
  addButtonText,
  onSearchFilterChange,
  topContent,
  mainContent,
  secondaryContent,
  sx,
}: PropsType) {
  const { t } = useTranslation();

  return (
    <Box
      sx={mergeSxProp(
        {
          width: 1,
          height: 1,
          display: "flex",
          flexDirection: "column",
        },
        sx,
      )}
    >
      {onSearchFilterChange && (
        <SearchFE onSearchValueChange={onSearchFilterChange} />
      )}
      {onAdd && (
        <Box sx={{ display: "flex", px: 1, mb: 1 }}>
          <Button
            color="primary"
            variant="contained"
            size="small"
            startIcon={<Add />}
            onClick={onAdd}
            sx={{
              display: "flex",
              justifyContent: "flex-start",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {addButtonText || t("global.add")}
          </Button>
        </Box>
      )}
      {topContent}
      {mainContent}
      {secondaryContent}
    </Box>
  );
}

export default PropertiesView;
