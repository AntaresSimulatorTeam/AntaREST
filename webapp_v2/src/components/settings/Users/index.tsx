import {
  Box,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Skeleton,
  Typography,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { useMemo, useReducer, useState } from "react";
import { useTranslation } from "react-i18next";
import PersonIcon from "@mui/icons-material/Person";
import produce from "immer";
import { usePromise as usePromiseWrapper, useUpdateEffect } from "react-use";
import { Action } from "redux";
import { useSnackbar } from "notistack";
import { deleteUser, getUsers } from "../../../services/api/user";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import Header from "./Header";
import { RESERVED_USER_NAMES, sortByName } from "./utils";
import { UserDetailsDTO } from "../../../common/types";

/**
 * Types
 */

enum UserActionKind {
  ADD = "ADD",
  DELETE = "DELETE",
  RESET = "RESET",
}

interface UserAction extends Action<string> {
  payload?: number | UserDetailsDTO | UserDetailsDTO[];
}

/**
 * Utils
 */

const reducer = produce<UserDetailsDTO[], [UserAction]>((draft, action) => {
  const { payload } = action;

  switch (action.type) {
    case UserActionKind.ADD: {
      draft.push(payload as UserDetailsDTO);
      return;
    }
    case UserActionKind.DELETE: {
      const index = draft.findIndex((user) => user.id === payload);
      if (index > -1) {
        draft.splice(index, 1);
      }
      return;
    }
    case UserActionKind.RESET:
      return payload as UserDetailsDTO[];
  }
});

/**
 * Component
 */

function Users() {
  const [userToDelete, setUserToDelete] = useState<UserDetailsDTO>();
  const [userInLoading, setUserInLoading] = useState<UserDetailsDTO>();
  const [users, dispatch] = useReducer(reducer, []);
  const [searchValue, setSearchValue] = useState("");
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();
  const { t } = useTranslation();

  const {
    data: initialUsers,
    isLoading,
    reload: reloadFetchUsers,
  } = usePromiseWithSnackbarError(async () => {
    const users = await getUsers<UserDetailsDTO>({ details: true });
    return users.filter((user) => !RESERVED_USER_NAMES.includes(user.name));
  }, "settings:usersError");

  useUpdateEffect(() => {
    dispatch({ type: UserActionKind.RESET, payload: initialUsers || [] });
  }, [initialUsers]);

  const filteredAndSortedUsers = useMemo(() => {
    let list = users;
    if (searchValue) {
      const searchVal = searchValue.toLowerCase();
      list = users?.filter((user) =>
        user.name.toLowerCase().includes(searchVal)
      );
    }
    return sortByName(list);
  }, [searchValue, users]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const addUser = (user: UserDetailsDTO) => {
    dispatch({ type: UserActionKind.ADD, payload: user });
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDeleteClick = (user: UserDetailsDTO) => () => {
    setUserToDelete(user);
  };

  const handleDeleteUser = () => {
    if (!userToDelete) {
      return;
    }

    const user = userToDelete;
    setUserInLoading(user);
    setUserToDelete(undefined);

    mounted(deleteUser(user.id))
      .then(() => {
        dispatch({ type: UserActionKind.DELETE, payload: user.id });
        enqueueSnackbar(t("settings:onUserDeleteSuccess", { user }), {
          variant: "success",
        });
      })
      .catch((err) => {
        enqueueErrorSnackbar(t("settings:onUserDeleteError", { user }), err);
      });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Header
        setSearchValue={setSearchValue}
        addUser={addUser}
        reloadFetchUsers={reloadFetchUsers}
      />
      <List>
        {/* Loading */}
        {isLoading &&
          Array.from({ length: 3 }, (v, k) => k).map((v) => (
            <ListItem key={v} disablePadding>
              <Skeleton sx={{ width: 1, height: 50 }} />
            </ListItem>
          ))}
        {/* User list */}
        {filteredAndSortedUsers?.map((user) => (
          <ListItem
            key={user.id}
            secondaryAction={
              userInLoading === user ? (
                <Box sx={{ display: "flex" }}>
                  <CircularProgress color="inherit" size={25} />
                </Box>
              ) : (
                <>
                  <IconButton>
                    <EditIcon />
                  </IconButton>
                  <IconButton edge="end" onClick={handleDeleteClick(user)}>
                    <DeleteIcon />
                  </IconButton>
                </>
              )
            }
            disablePadding
          >
            <ListItemButton>
              <ListItemIcon>
                <PersonIcon />
              </ListItemIcon>
              <ListItemText primary={user.name} />
            </ListItemButton>
          </ListItem>
        ))}
        {/* No user */}
        {filteredAndSortedUsers && filteredAndSortedUsers.length === 0 && (
          <Typography sx={{ m: 2 }} align="center">
            {t("settings:noUser")}
          </Typography>
        )}
      </List>
      {userToDelete && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setUserToDelete(undefined)}
          onConfirm={handleDeleteUser}
          alert="warning"
          open
        >
          {t("settings:deleteUserConfirmation")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default Users;
