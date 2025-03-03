/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

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
import { produce } from "immer";
import { usePromise as usePromiseWrapper, useUpdateEffect } from "react-use";
import type { Action } from "redux";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { deleteUser, getUsers } from "../../../../services/api/user";
import usePromiseWithSnackbarError from "../../../../hooks/usePromiseWithSnackbarError";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import ConfirmationDialog from "../../../common/dialogs/ConfirmationDialog";
import Header from "./Header";
import { RESERVED_USER_NAMES } from "../utils";
import type { UserDetailsDTO } from "../../../../types/types";
import UpdateUserDialog from "./dialog/UpdateUserDialog";
import { sortByName } from "../../../../services/utils";
import { isSearchMatching } from "../../../../utils/stringUtils";

enum UserActionKind {
  ADD = "ADD",
  EDIT = "EDIT",
  DELETE = "DELETE",
  RESET = "RESET",
}

export type UserEdit = Partial<UserDetailsDTO> & { id: UserDetailsDTO["id"] };

interface UserAction extends Action<string> {
  payload?: UserDetailsDTO["id"] | UserDetailsDTO | UserDetailsDTO[] | UserEdit;
}

const reducer = produce<UserDetailsDTO[], [UserAction]>((draft, action) => {
  const { payload } = action;

  switch (action.type) {
    case UserActionKind.ADD: {
      draft.push(payload as UserDetailsDTO);
      return;
    }
    case UserActionKind.EDIT: {
      const { id, ...newData } = payload as UserEdit;
      const index = draft.findIndex((user) => user.id === id);
      if (index > -1) {
        draft[index] = { ...draft[index], ...newData };
      }
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

function Users() {
  const [userToDelete, setUserToDelete] = useState<UserDetailsDTO>();
  const [userToEdit, setUserToEdit] = useState<UserDetailsDTO>();
  const [usersInLoading, setUsersInLoading] = useState<UserDetailsDTO[]>([]);
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
  } = usePromiseWithSnackbarError(() => getUsers({ details: true }), {
    errorMessage: t("settings.error.usersError"),
  });

  useUpdateEffect(() => {
    setUserToDelete(undefined);
    setUserToEdit(undefined);
    setUsersInLoading([]);

    dispatch({ type: UserActionKind.RESET, payload: initialUsers || [] });
  }, [initialUsers]);

  const filteredAndSortedUsers = useMemo(() => {
    let list = users.filter((u) => !RESERVED_USER_NAMES.includes(u.name));
    if (searchValue) {
      list = users?.filter((user) => isSearchMatching(searchValue, user.name));
    }
    return sortByName(list);
  }, [searchValue, users]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const addUser = (user: UserDetailsDTO) => {
    dispatch({ type: UserActionKind.ADD, payload: user });
  };

  const editUser = (user: UserEdit) => {
    dispatch({ type: UserActionKind.EDIT, payload: user });
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDeleteUser = () => {
    if (!userToDelete) {
      return;
    }

    const user = userToDelete;
    setUsersInLoading((prev) => [...prev, user]);
    setUserToDelete(undefined);

    mounted(deleteUser(user.id))
      .then(() => {
        dispatch({ type: UserActionKind.DELETE, payload: user.id });
        enqueueSnackbar(t("settings.success.userDelete", { 0: user.name }), {
          variant: "success",
        });
      })
      .catch((err) => {
        enqueueErrorSnackbar(t("settings.error.userDelete", { 0: user.name }), err);
      })
      .finally(() => {
        setUsersInLoading((prev) => prev.filter((u) => u !== user));
      });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: 1,
      }}
    >
      <Header
        setSearchValue={setSearchValue}
        addUser={addUser}
        reloadFetchUsers={reloadFetchUsers}
      />
      <List sx={{ overflow: "auto" }}>
        {R.cond([
          // Loading
          [
            () => isLoading,
            () =>
              Array.from({ length: 3 }, (v, k) => k).map((v) => (
                <ListItem key={v} disablePadding>
                  <Skeleton sx={{ width: 1, height: 50 }} />
                </ListItem>
              )) as React.ReactNode,
          ],
          // User list
          [
            () => filteredAndSortedUsers.length > 0,
            () =>
              filteredAndSortedUsers.map((user) => (
                <ListItem
                  key={user.id}
                  secondaryAction={
                    usersInLoading.includes(user) ? (
                      <Box sx={{ display: "flex" }}>
                        <CircularProgress color="inherit" size={25} />
                      </Box>
                    ) : (
                      <>
                        <IconButton onClick={() => setUserToEdit(user)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton edge="end" onClick={() => setUserToDelete(user)}>
                          <DeleteIcon />
                        </IconButton>
                      </>
                    )
                  }
                  disablePadding
                >
                  <ListItemButton onClick={() => setUserToEdit(user)}>
                    <ListItemIcon>
                      <PersonIcon />
                    </ListItemIcon>
                    <ListItemText primary={user.name} />
                  </ListItemButton>
                </ListItem>
              )),
          ],
          // No user
          [
            R.T,
            () => (
              <Typography sx={{ m: 2 }} align="center">
                {t("settings.noUser")}
              </Typography>
            ),
          ],
        ])()}
      </List>
      {userToDelete && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setUserToDelete(undefined)}
          onConfirm={handleDeleteUser}
          alert="warning"
          open
        >
          {t("settings.question.deleteUser", { 0: userToDelete.name })}
        </ConfirmationDialog>
      )}
      {userToEdit && (
        <UpdateUserDialog
          open
          user={userToEdit}
          editUser={editUser}
          reloadFetchUsers={reloadFetchUsers}
          closeDialog={() => setUserToEdit(undefined)}
        />
      )}
    </Box>
  );
}

export default Users;
