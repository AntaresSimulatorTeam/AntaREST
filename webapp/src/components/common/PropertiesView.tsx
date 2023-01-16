import { ReactNode } from "react";
import { Box, Fab, SxProps, Theme } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import SearchFE from "./fieldEditors/SearchFE";
import { mergeSxProp } from "../../utils/muiUtils";

interface PropsType {
  mainContent: ReactNode | undefined;
  secondaryContent?: ReactNode;
  onSearchFilterChange?: (value: string) => void;
  onAdd?: () => void;
  sx?: SxProps<Theme>;
}

function PropertiesView(props: PropsType) {
  const { onAdd, onSearchFilterChange, mainContent, secondaryContent, sx } =
    props;

  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      sx={mergeSxProp(
        {
          pt: onSearchFilterChange ? 1 : 2,
          pb: 1,
        },
        sx
      )}
    >
      {onSearchFilterChange && (
        <SearchFE onSearchValueChange={onSearchFilterChange} />
      )}
      {mainContent}
      {secondaryContent}
      {onAdd && (
        <Fab
          size="small"
          color="primary"
          aria-label="add"
          sx={{ alignSelf: "flex-start", mb: 2, ml: 1 }}
          onClick={onAdd}
        >
          <AddIcon />
        </Fab>
      )}
    </Box>
  );
}

PropertiesView.defaultProps = {
  onAdd: undefined,
};

export default PropertiesView;
