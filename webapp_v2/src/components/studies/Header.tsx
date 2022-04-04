import React, { useState } from "react";
import { styled, useTheme } from "@mui/material/styles";
import { purple, indigo } from "@mui/material/colors";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import TextField from "@mui/material/TextField";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Divider,
  InputAdornment,
  Typography,
  Chip,
} from "@mui/material";
import { STUDIES_HEIGHT_HEADER } from "../../theme";
import ImportStudy from "./ImportStudy";
import CreateStudyModal from "./CreateStudyModal";
import { GenericInfo, GroupDTO, UserDTO } from "../../common/types";

const Root = styled("div")(({ theme }) => ({
  width: "100%",
  height: `${STUDIES_HEIGHT_HEADER}px`,
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: theme.spacing(2, 0),
  boxSizing: "border-box",
}));

const Searchbar = styled(TextField)(({ theme }) => ({
  color: theme.palette.grey[400],
  "& .MuiOutlinedInput-root": {
    height: "40px",
    "&.Mui-focused fieldset": {},
  },
}));

interface Props {
  inputValue: string;
  setInputValue: (value: string) => void;
  onFilterClick: () => void;
  managedFilter: boolean;
  versions: Array<GenericInfo> | undefined;
  users: Array<UserDTO> | undefined;
  groups: Array<GroupDTO> | undefined;
  tags: Array<string> | undefined;
  setManageFilter: (value: boolean) => void;
  setVersions: (value: Array<GenericInfo> | undefined) => void;
  setUsers: (value: Array<UserDTO> | undefined) => void;
  setGroups: (value: Array<GroupDTO> | undefined) => void;
  setTags: (value: Array<string> | undefined) => void;
}

function Header(props: Props) {
  const [t] = useTranslation();
  const theme = useTheme();
  const {
    inputValue,
    managedFilter,
    users,
    versions,
    groups,
    tags,
    setInputValue,
    setVersions,
    setUsers,
    setGroups,
    setTags,
    onFilterClick,
    setManageFilter,
  } = props;
  const [openCreateModal, setOpenCreateModal] = useState<boolean>(false);

  return (
    <Root>
      <Box width="100%" alignItems="center" display="flex" px={3}>
        <Box alignItems="center" display="flex">
          <TravelExploreOutlinedIcon
            sx={{ color: "text.secondary", width: "42px", height: "42px" }}
          />
          <Typography color="white" sx={{ ml: 2, fontSize: "34px" }}>
            {t("main:studies")}
          </Typography>
        </Box>
        <Box
          alignItems="center"
          justifyContent="flex-end"
          flexGrow={1}
          display="flex"
        >
          <ImportStudy />
          <Button
            sx={{ m: 2 }}
            variant="contained"
            color="primary"
            startIcon={<AddCircleOutlineOutlinedIcon />}
            onClick={() => setOpenCreateModal(true)}
          >
            {t("main:create")}
          </Button>
          {openCreateModal && (
            <CreateStudyModal
              open={openCreateModal}
              onClose={() => setOpenCreateModal(false)}
            />
          )}
        </Box>
      </Box>
      <Box display="flex" width="100%" alignItems="center" py={2} px={3}>
        <Box display="flex" width="100%" alignItems="center">
          <Searchbar
            id="standard-basic"
            value={inputValue}
            variant="outlined"
            sx={{ height: "40px" }}
            onChange={(event) => setInputValue(event.target.value as string)}
            label={t("main:search")}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchOutlinedIcon />
                </InputAdornment>
              ),
              sx: {
                ".MuiOutlinedInput-root": {
                  "&.MuiOutlinedInput-notchedOutline": {
                    borderColor: `${theme.palette.primary.main} !important`,
                  },
                },
                ".Mui-focused": {
                  // borderColor: `${theme.palette.primary.main} !important`
                },
                ".MuiOutlinedInput-notchedOutline": {
                  borderWidth: "1px",
                  borderColor: `${theme.palette.text.secondary} !important`,
                },
              },
            }}
            InputLabelProps={{
              sx: {
                ".MuiInputLabel-root": {
                  color: theme.palette.text.secondary,
                },
                ".Mui-focused": {},
              },
            }}
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
            {t("main:filter")}
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
                label={t("studymanager:managedStudiesFilter")}
                variant="filled"
                color="secondary"
                onDelete={() => setManageFilter(false)}
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
                    setVersions(
                      newVersions.length > 0 ? newVersions : undefined
                    );
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
                    const newGroups = groups.filter(
                      (item) => item.id !== elm.id
                    );
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
      </Box>
    </Root>
  );
}

export default Header;
