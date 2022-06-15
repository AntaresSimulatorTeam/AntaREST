import { ReactNode } from "react";
import { TextField, InputAdornment, Box, Fab } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { useTranslation } from "react-i18next";
import AddIcon from "@mui/icons-material/Add";

interface PropsType {
  mainContent: ReactNode | undefined;
  secondaryContent?: ReactNode;
  onSearchFilterChange?: (value: string) => void;
  onAdd?: () => void;
}

function PropertiesView(props: PropsType) {
  const { onAdd, onSearchFilterChange, mainContent, secondaryContent } = props;
  const [t] = useTranslation();

  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      sx={{
        pt: onSearchFilterChange ? 1 : 2,
        pb: 1,
      }}
    >
      {onSearchFilterChange && (
        <TextField
          label={t("global.search")}
          variant="outlined"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          onChange={(e) => onSearchFilterChange(e.target.value as string)}
        />
      )}
      {mainContent}
      {secondaryContent}
      {onAdd && (
        <Fab
          size="small"
          color="primary"
          aria-label="add"
          sx={{ alignSelf: "flex-start", mb: 2, ml: 1 }}
        >
          <AddIcon onClick={onAdd} />
        </Fab>
      )}
    </Box>
  );
}

PropertiesView.defaultProps = {
  onAdd: undefined,
};

export default PropertiesView;
