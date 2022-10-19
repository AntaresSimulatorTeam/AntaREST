import { Box, Button, Chip, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import { indigo, purple } from "@mui/material/colors";
import useDebounce from "../../../hooks/useDebounce";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getGroups, getStudyFilters, getUsers } from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { StudyFilters, updateStudyFilters } from "../../../redux/ducks/studies";
import { GroupDTO, UserDTO } from "../../../common/types";
import { displayVersionName } from "../../../services/utils";
import SearchFE from "../../common/fieldEditors/SearchFE";

type PropTypes = {
  onOpenFilterClick: VoidFunction;
};

function HeaderBottom(props: PropTypes) {
  const { onOpenFilterClick } = props;
  const filters = useAppSelector(getStudyFilters);
  const dispatch = useAppDispatch();
  const [t] = useTranslation();

  const users = useAppSelector((state) => {
    return getUsers(state)
      .filter((user) => filters.users.includes(user.id))
      .map((user) => ({ id: user.id, name: user.name } as UserDTO));
  });

  const groups = useAppSelector((state) => {
    return getGroups(state)
      .filter((group) => filters.groups.includes(group.id))
      .map((group) => ({ id: group.id, name: group.name } as GroupDTO));
  });

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
      <SearchFE
        sx={{ mx: 0 }}
        defaultValue={filters.inputValue}
        onChange={handleSearchChange}
        useLabel
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
        {filters.variant && (
          <Chip
            label={t("studies.variant").toLowerCase()}
            color="secondary"
            onDelete={() => setFilterValue("variant", false)}
            sx={{ mx: 1 }}
          />
        )}
        {filters.versions.map((version) => (
          <Chip
            key={version}
            label={displayVersionName(version)}
            variant="filled"
            color="primary"
            onDelete={() => {
              setFilterValue(
                "versions",
                filters.versions.filter((ver) => ver !== version)
              );
            }}
            sx={{ mx: 1 }}
          />
        ))}
        {users.map((user, _) => (
          <Chip
            key={user.id}
            label={user.name}
            variant="filled"
            onDelete={() => {
              setFilterValue(
                "users",
                filters.users.filter((u) => u !== user.id)
              );
            }}
            sx={{ mx: 1, bgcolor: purple[500] }}
          />
        ))}
        {groups.map((group, _) => (
          <Chip
            key={group.id}
            label={group.name}
            variant="filled"
            color="success"
            onDelete={() => {
              setFilterValue(
                "groups",
                filters.groups.filter((gp) => gp !== group.id)
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
