import { useTranslation } from "react-i18next";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Divider from "@mui/material/Divider";
import {
  Button,
  Checkbox,
  Drawer,
  FormControlLabel,
  Typography,
} from "@mui/material";
import { STUDIES_FILTER_WIDTH } from "../../theme";
import useAppSelector from "../../redux/hooks/useAppSelector";
import { getStudyFilters } from "../../redux/selectors";
import useAppDispatch from "../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../redux/ducks/studies";

interface Props {
  open: boolean;
  onClose: () => void;
}

function FilterDrawer(props: Props) {
  const { open, onClose } = props;
  const [t] = useTranslation();
  const filters = useAppSelector(getStudyFilters);
  //   const versions = useAppSelector(getStudyVersions);
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const target = event.target as typeof event.target & {
      managed: { checked: boolean };
      archived: { checked: boolean };
    };

    dispatch(
      updateStudyFilters({
        managed: target.managed.checked,
        archived: target.archived.checked,
        // versions: [],
        // users: [],
        // groups: [],
        // tags: [],
      })
    );

    onClose();
  };

  const handleReset = () => {
    dispatch(
      updateStudyFilters({
        managed: false,
        archived: false,
        versions: [],
        users: [],
        groups: [],
        tags: [],
      })
    );

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
      <form onSubmit={handleSubmit}>
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
            <Typography sx={{ color: "grey.500", fontSize: "0.9em", mb: 2 }}>
              {t("global.filter").toUpperCase()}
            </Typography>
            <FormControlLabel
              control={
                <Checkbox
                  name="managed"
                  defaultChecked={filters.managed}
                  sx={{ color: "white" }}
                />
              }
              label={t("studies.managedStudiesFilter") as string}
            />
            <FormControlLabel
              control={
                <Checkbox
                  name="archived"
                  defaultChecked={filters.archived}
                  sx={{ color: "white" }}
                />
              }
              label={t("studies.archivedStudiesFilter") as string}
            />
          </Box>
        </Toolbar>
        <Divider style={{ height: "1px", backgroundColor: "grey.800" }} />
        {/* <List>
        <ListItem>
          <SelectMulti
            name={t("global.versions")}
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
                label={t("global.users")}
              />
            )}
          />
        </ListItem>
        <ListItem>
          <SelectMulti
            name={t("global.groups")}
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
            label={t("global.tags")}
            sx={{ m: 1, width: "200px" }}
            value={currentTags || []}
            onChange={setCurrentTags}
            tagList={tagList}
          />
        </ListItem>
      </List> */}
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
            <Button variant="outlined" onClick={handleReset}>
              {t("global.reset")}
            </Button>
            <Button sx={{ mx: 2 }} variant="contained" type="submit">
              {t("global.filter")}
            </Button>
          </Box>
        </Box>
      </form>
    </Drawer>
  );
}

export default FilterDrawer;
