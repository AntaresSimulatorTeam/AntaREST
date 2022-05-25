import {
  Box,
  Button,
  Chip,
  Divider,
  InputAdornment,
  TextField,
} from "@mui/material";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import { useTranslation } from "react-i18next";
import { indigo, purple } from "@mui/material/colors";
import useDebounce from "../../hooks/useDebounce";
import useAppSelector from "../../redux/hooks/useAppSelector";
import { getStudyFilters } from "../../redux/selectors";
import useAppDispatch from "../../redux/hooks/useAppDispatch";
import { StudyFilters, updateStudyFilters } from "../../redux/ducks/studies";

type PropTypes = {
  onOpenFilterClick: VoidFunction;
};

function HeaderBottom(props: PropTypes) {
  const { onOpenFilterClick } = props;
  const filters = useAppSelector(getStudyFilters);
  const dispatch = useAppDispatch();
  const [t] = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const setFilterValue = <T extends keyof StudyFilters>(
    string: T,
    newValue: StudyFilters[T]
  ) => {
    dispatch(updateStudyFilters({ [string]: newValue }));
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSearchChange = useDebounce(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setFilterValue("inputValue", event.target.value);
    },
    150
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box display="flex" width="100%" alignItems="center">
      <TextField
        id="standard-basic"
        variant="outlined"
        defaultValue={filters.inputValue}
        onChange={handleSearchChange}
        label={t("global.search")}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchOutlinedIcon />
            </InputAdornment>
          ),
        }}
        sx={{ mx: 0 }}
      />
      <Divider
        sx={{
          width: "1px",
          height: "40px",
          bgcolor: "divider",
          margin: "0px 16px",
        }}
      />
      <Button color="secondary" variant="outlined" onClick={onOpenFilterClick}>
        {t("global.filter")}
      </Button>
      <Box
        flex={1}
        display="flex"
        flexDirection="row"
        justifyContent="flex-start"
        alignItems="center"
        px={2}
        sx={{ overflowX: "auto", overflowY: "hidden" }}
      >
        {filters.managed && (
          <Chip
            label={t("studies.managedStudiesFilter")}
            variant="filled"
            color="secondary"
            onDelete={() => setFilterValue("managed", false)}
            sx={{ mx: 1 }}
          />
        )}
        {filters.archived && (
          <Chip
            label={t("studies.archivedStudiesFilter")}
            variant="filled"
            color="secondary"
            onDelete={() => setFilterValue("archived", false)}
            sx={{ mx: 1 }}
          />
        )}
        {filters.versions.map((version, _, versions) => (
          <Chip
            key={version.id}
            label={version.name}
            variant="filled"
            color="primary"
            onDelete={() => {
              setFilterValue(
                "versions",
                versions.filter((ver) => ver !== version)
              );
            }}
            sx={{ mx: 1 }}
          />
        ))}
        {filters.users.map((userId, _, users) => (
          <Chip
            key={userId}
            label={userId} // TODO
            variant="filled"
            onDelete={() => {
              setFilterValue(
                "users",
                users.filter((u) => u !== userId)
              );
            }}
            sx={{ mx: 1, bgcolor: purple[500] }}
          />
        ))}
        {filters.groups.map((groupId, _, groups) => (
          <Chip
            key={groupId}
            label={groupId}
            variant="filled"
            color="success"
            onDelete={() => {
              setFilterValue(
                "groups",
                groups.filter((gp) => gp !== groupId)
              );
            }}
            sx={{ mx: 1 }}
          />
        ))}
        {filters.tags.map((tag, _, tags) => (
          <Chip
            key={tag}
            label={tag}
            variant="filled"
            onDelete={() => {
              setFilterValue(
                "tags",
                tags.filter((t) => t !== tag)
              );
            }}
            sx={{ mx: 1, color: "black", bgcolor: indigo[300] }}
          />
        ))}
      </Box>
    </Box>
  );
}

export default HeaderBottom;
