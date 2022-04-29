import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import List from "@mui/material/List";
import Divider from "@mui/material/Divider";
import {
  Autocomplete,
  Button,
  Checkbox,
  Drawer,
  FormControlLabel,
  ListItem,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import CheckBoxOutlineBlankIcon from "@mui/icons-material/CheckBoxOutlineBlank";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import { STUDIES_FILTER_WIDTH } from "../../theme";
import SelectMulti from "../common/SelectMulti";
import { GenericInfo, GroupDTO, UserDTO } from "../../common/types";
import { convertVersions } from "../../services/utils";
import TagTextInput from "../common/TagTextInput";

interface Props {
  open: boolean;
  managedFilter: boolean;
  archivedFilter: boolean;
  versionList: Array<GenericInfo>;
  versions: Array<GenericInfo>;
  tagList: Array<string>;
  tags: Array<string>;
  userList: Array<UserDTO>;
  users: Array<UserDTO>;
  groupList: Array<GroupDTO>;
  groups: Array<GroupDTO>;
  onFilterActionClick: (
    managed: boolean,
    archived: boolean,
    versions: Array<GenericInfo> | undefined,
    users: Array<UserDTO> | undefined,
    groups: Array<GroupDTO> | undefined,
    tags: Array<string> | undefined
  ) => void;
  onClose: () => void;
}

function FilterDrawer(props: Props) {
  const theme = useTheme();
  const [t] = useTranslation();
  const {
    open,
    managedFilter,
    archivedFilter,
    tagList,
    tags,
    versionList,
    versions,
    userList,
    users,
    groupList,
    groups,
    onFilterActionClick,
    onClose,
  } = props;

  const [currentUsers, setCurrentUsers] = useState<Array<UserDTO> | undefined>(
    users
  );
  const [currentGroups, setCurrentGroups] = useState<
    Array<GroupDTO> | undefined
  >(groups);
  const [currentVersions, setCurrentVersions] = useState<
    Array<GenericInfo> | undefined
  >(versions);
  const [currentTags, setCurrentTags] = useState<Array<string> | undefined>(
    tags
  );
  const [currentManaged, setCurrentManaged] = useState<boolean>(managedFilter);
  const [currentArchived, setCurrentArchived] =
    useState<boolean>(archivedFilter);

  useEffect(() => {
    setCurrentUsers(users);
  }, [users]);
  useEffect(() => {
    setCurrentGroups(groups);
  }, [groups]);
  useEffect(() => {
    setCurrentVersions(versions);
  }, [versions]);
  useEffect(() => {
    setCurrentTags(tags);
  }, [tags]);
  useEffect(() => {
    setCurrentManaged(managedFilter);
  }, [managedFilter]);

  const setVersions = (data: Array<string>): void => {
    if (data.length === 0) {
      setCurrentVersions(undefined);
      return;
    }
    setCurrentVersions(convertVersions(data || []));
  };

  const setUsers = (data: Array<string>): void => {
    if (data.length === 0) {
      setCurrentUsers(undefined);
      return;
    }
    setCurrentUsers(
      data.map((elm) => {
        const index = userList.findIndex((item) => item.id.toString() === elm);
        return { id: userList[index].id, name: userList[index].name };
      })
    );
  };

  const setGroups = (data: Array<string>): void => {
    if (data.length === 0) {
      setCurrentGroups(undefined);
      return;
    }
    setCurrentGroups(
      data.map((elm) => {
        const index = groupList.findIndex((item) => item.id === elm);
        return { id: groupList[index].id, name: groupList[index].name };
      })
    );
  };

  const setArchived = (data: boolean): void => {
    setCurrentArchived(data);
  };

  const setManaged = (data: boolean): void => {
    setCurrentManaged(data);
    if (!data) setArchived(false);
  };

  const onFilterClick = (): void => {
    onFilterActionClick(
      currentManaged,
      currentArchived,
      currentVersions,
      currentUsers,
      currentGroups,
      currentTags
    );
  };

  const onResetFilterClick = (): void => {
    setCurrentVersions(undefined);
    setCurrentUsers(undefined);
    setCurrentGroups(undefined);
    setCurrentTags(undefined);
    setManaged(false);
    setArchived(false);
  };

  return (
    <Drawer
      variant="temporary"
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        width: STUDIES_FILTER_WIDTH,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: STUDIES_FILTER_WIDTH,
          boxSizing: "border-box",
          overflow: "hidden",
        },
      }}
    >
      <Toolbar sx={{ py: 3 }}>
        <Box
          display="flex"
          width="100%"
          height="100%"
          justifyContent="flex-start"
          alignItems="flex-start"
          py={2}
          flexDirection="column"
          flexWrap="nowrap"
          boxSizing="border-box"
          color="white"
        >
          <Typography
            sx={{ color: "grey.500", fontSize: "0.9em", mb: theme.spacing(2) }}
          >
            {t("main:filter").toUpperCase()}
          </Typography>
          <FormControlLabel
            control={
              <Checkbox
                checked={currentManaged}
                onChange={() => setManaged(!currentManaged)}
                sx={{ color: "white" }}
              />
            }
            label={t("studymanager:managedStudiesFilter") as string}
          />
          {currentManaged && (
            <FormControlLabel
              control={
                <Checkbox
                  checked={currentArchived}
                  onChange={() => setArchived(!currentArchived)}
                  sx={{ color: "white" }}
                />
              }
              label={t("studymanager:archivedStudiesFilter") as string}
            />
          )}
        </Box>
      </Toolbar>
      <Divider
        style={{ height: "1px", backgroundColor: theme.palette.grey[800] }}
      />
      <List>
        <ListItem>
          <SelectMulti
            name={t("studymanager:versionsLabel")}
            list={versionList}
            data={
              currentVersions !== undefined
                ? currentVersions.map((elm) => elm.id as string)
                : []
            }
            setValue={setVersions}
          />
        </ListItem>
        <ListItem>
          <Autocomplete
            multiple
            id="study-filter-users"
            options={userList || []}
            value={currentUsers || []}
            getOptionLabel={(option: UserDTO) => option.name}
            sx={{ width: 200, m: 1 }}
            renderOption={(props, option, { selected }) => (
              <li {...props}>
                <Checkbox
                  icon={<CheckBoxOutlineBlankIcon fontSize="small" />}
                  checkedIcon={<CheckBoxIcon fontSize="small" />}
                  style={{ marginRight: 8 }}
                  checked={selected}
                />
                {option.name}
              </li>
            )}
            onChange={(event, value) =>
              setUsers(value.map((el) => el.id.toString()))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                variant="filled"
                sx={{
                  background: "rgba(255, 255, 255, 0.09)",
                  borderRadius: "4px 4px 0px 0px",
                  borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
                  ".MuiIconButton-root": {
                    backgroundColor: "#222333",
                    padding: 0,
                    marginTop: "2px",
                  },
                }}
                label={t("studymanager:usersLabel")}
              />
            )}
          />
        </ListItem>
        <ListItem>
          <SelectMulti
            name={t("studymanager:groupsLabel")}
            list={groupList.map((elm) => ({ id: elm.id, name: elm.name }))}
            data={
              currentGroups !== undefined
                ? currentGroups.map((elm) => elm.id)
                : []
            }
            setValue={setGroups}
          />
        </ListItem>
        <ListItem>
          <TagTextInput
            label={t("studymanager:tagsLabel")}
            sx={{ m: 1, width: "200px" }}
            value={currentTags || []}
            onChange={setCurrentTags}
            tagList={tagList}
          />
        </ListItem>
      </List>
      <Box
        display="flex"
        width="100%"
        flexGrow={1}
        justifyContent="flex-end"
        alignItems="center"
        flexDirection="column"
        flexWrap="nowrap"
        boxSizing="border-box"
      >
        <Box
          display="flex"
          width="100%"
          height="auto"
          justifyContent="flex-end"
          alignItems="center"
          flexDirection="row"
          flexWrap="nowrap"
          boxSizing="border-box"
          p={1}
        >
          <Button variant="text" color="primary" onClick={onResetFilterClick}>
            {t("main:reset")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="success"
            variant="contained"
            onClick={onFilterClick}
          >
            {t("main:filter")}
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
}

export default FilterDrawer;
