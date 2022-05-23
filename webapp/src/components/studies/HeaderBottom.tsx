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
import { GenericInfo, GroupDTO, UserDTO } from "../../common/types";

/**
 * Types
 */

type PropTypes = {
  inputValue: string;
  setInputValue: (value: string) => void;
  onFilterClick: () => void;
  managedFilter: boolean;
  archivedFilter: boolean;
  versions: Array<GenericInfo> | undefined;
  users: Array<UserDTO> | undefined;
  groups: Array<GroupDTO> | undefined;
  tags: Array<string> | undefined;
  setManageFilter: (value: boolean) => void;
  setArchivedFilter: (value: boolean) => void;
  setVersions: (value: Array<GenericInfo> | undefined) => void;
  setUsers: (value: Array<UserDTO> | undefined) => void;
  setGroups: (value: Array<GroupDTO> | undefined) => void;
  setTags: (value: Array<string> | undefined) => void;
};

/**
 * Component
 */

function HeaderBottom(props: PropTypes) {
  const {
    inputValue,
    setInputValue,
    onFilterClick,
    managedFilter,
    setManageFilter,
    archivedFilter,
    setArchivedFilter,
    versions,
    setVersions,
    users,
    setUsers,
    groups,
    setGroups,
    tags,
    setTags,
  } = props;

  const [t] = useTranslation();

  const handleManagedDeletion = () => {
    setManageFilter(false);
    setArchivedFilter(false);
  };

  return (
    <Box display="flex" width="100%" alignItems="center">
      <TextField
        id="standard-basic"
        value={inputValue}
        variant="outlined"
        onChange={(event) => setInputValue(event.target.value as string)}
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
      <Button color="secondary" variant="outlined" onClick={onFilterClick}>
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
        {managedFilter && (
          <Chip
            label={t("studies.managedStudiesFilter")}
            variant="filled"
            color="secondary"
            onDelete={handleManagedDeletion}
            sx={{ mx: 1 }}
          />
        )}
        {archivedFilter && (
          <Chip
            label={t("studies.archivedStudiesFilter")}
            variant="filled"
            color="secondary"
            onDelete={() => setArchivedFilter(false)}
            sx={{ mx: 1 }}
          />
        )}
        {versions &&
          versions.map((elm) => (
            <Chip
              key={elm.id}
              label={elm.name}
              variant="filled"
              color="primary"
              onDelete={() => {
                const newVersions = versions.filter(
                  (item) => item.id !== elm.id
                );
                setVersions(newVersions.length > 0 ? newVersions : undefined);
              }}
              sx={{ mx: 1 }}
            />
          ))}
        {users &&
          users.map((elm) => (
            <Chip
              key={elm.id}
              label={elm.name}
              variant="filled"
              onDelete={() => {
                const newUsers = users.filter((item) => item.id !== elm.id);
                setUsers(newUsers.length > 0 ? newUsers : undefined);
              }}
              sx={{ mx: 1, bgcolor: purple[500] }}
            />
          ))}
        {groups &&
          groups.map((elm) => (
            <Chip
              key={elm.id}
              label={elm.name}
              variant="filled"
              color="success"
              onDelete={() => {
                const newGroups = groups.filter((item) => item.id !== elm.id);
                setGroups(newGroups.length > 0 ? newGroups : undefined);
              }}
              sx={{ mx: 1 }}
            />
          ))}
        {tags &&
          tags.map((elm) => (
            <Chip
              key={elm}
              label={elm}
              variant="filled"
              onDelete={() => {
                const newTags = tags.filter((item) => item !== elm);
                setTags(newTags.length > 0 ? newTags : undefined);
              }}
              sx={{ mx: 1, color: "black", bgcolor: indigo[300] }}
            />
          ))}
      </Box>
    </Box>
  );
}

export default HeaderBottom;
