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
import produce from "immer";
import { ReactNode, useMemo, useReducer, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper, useUpdateEffect } from "react-use";
import { Action } from "redux";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import * as R from "ramda";
import GroupIcon from "@mui/icons-material/Group";
import { useSnackbar } from "notistack";
import { GroupDetailsDTO } from "../../../../common/types";
import usePromiseWithSnackbarError from "../../../../hooks/usePromiseWithSnackbarError";
import { deleteGroup, getGroups } from "../../../../services/api/user";
import { sortByName } from "../../../../services/utils";
import ConfirmationDialog from "../../../common/dialogs/ConfirmationDialog";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import { RESERVED_GROUP_NAMES } from "../utils";
import Header from "./Header";
import UpdateGroupDialog from "./dialog/UpdateGroupDialog";
import { getAuthUser } from "../../../../redux/selectors";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { isSearchMatching } from "../../../../utils/textUtils";

/**
 * Types
 */

enum GroupActionKind {
  ADD = "ADD",
  EDIT = "EDIT",
  DELETE = "DELETE",
  RESET = "RESET",
}

export type GroupEdit = Partial<GroupDetailsDTO> & {
  id: GroupDetailsDTO["id"];
};

interface GroupAction extends Action<string> {
  payload?:
    | GroupDetailsDTO["id"]
    | GroupDetailsDTO
    | GroupDetailsDTO[]
    | GroupEdit;
}

/**
 * Utils
 */

const reducer = produce<GroupDetailsDTO[], [GroupAction]>((draft, action) => {
  const { payload } = action;

  switch (action.type) {
    case GroupActionKind.ADD: {
      draft.push(payload as GroupDetailsDTO);
      return;
    }
    case GroupActionKind.EDIT: {
      const { id, ...newData } = payload as GroupEdit;
      const index = draft.findIndex((group) => group.id === id);
      if (index > -1) {
        draft[index] = { ...draft[index], ...newData };
      }
      return;
    }
    case GroupActionKind.DELETE: {
      const index = draft.findIndex((group) => group.id === payload);
      if (index > -1) {
        draft.splice(index, 1);
      }
      return;
    }
    case GroupActionKind.RESET:
      return payload as GroupDetailsDTO[];
  }
});

/**
 * Component
 */

function Groups() {
  const [groupToDelete, setGroupToDelete] = useState<GroupDetailsDTO>();
  const [groupToEdit, setGroupToEdit] = useState<GroupDetailsDTO>();
  const [groupsInLoading, setGroupsInLoading] = useState<GroupDetailsDTO[]>([]);
  const [groups, dispatch] = useReducer(reducer, []);
  const [searchValue, setSearchValue] = useState("");
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();
  const { t } = useTranslation();
  const authUser = useAppSelector(getAuthUser);

  const {
    data: initialGroups,
    isLoading,
    reload: reloadFetchGroups,
  } = usePromiseWithSnackbarError(() => getGroups({ details: true }), {
    errorMessage: t("settings.error.groupsError"),
  });

  useUpdateEffect(() => {
    setGroupToDelete(undefined);
    setGroupToEdit(undefined);
    setGroupsInLoading([]);

    dispatch({ type: GroupActionKind.RESET, payload: initialGroups || [] });
  }, [initialGroups]);

  const filteredAndSortedGroups = useMemo(() => {
    let list = groups
      .filter((gp) => !RESERVED_GROUP_NAMES.includes(gp.name))
      .map((gp) => ({
        ...gp,
        users: gp.users.filter((user) => user.id !== authUser?.id),
      }));

    if (searchValue) {
      list = groups?.filter((group) => {
        return isSearchMatching(searchValue, group.name);
      });
    }
    return sortByName(list);
  }, [searchValue, groups, authUser]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const addGroup = (group: GroupDetailsDTO) => {
    dispatch({ type: GroupActionKind.ADD, payload: group });
  };

  const editGroup = (group: GroupEdit) => {
    dispatch({ type: GroupActionKind.EDIT, payload: group });
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDeleteGroup = () => {
    if (!groupToDelete) {
      return;
    }

    const group = groupToDelete;
    setGroupsInLoading((prev) => [...prev, group]);
    setGroupToDelete(undefined);

    mounted(deleteGroup(group.id))
      .then(() => {
        dispatch({ type: GroupActionKind.DELETE, payload: group.id });
        enqueueSnackbar(t("settings.success.groupDelete", [group.name]), {
          variant: "success",
        });
      })
      .catch((err) => {
        enqueueErrorSnackbar(
          t("settings.error.groupDelete", [group.name]),
          err
        );
      })
      .finally(() => {
        setGroupsInLoading((prev) => prev.filter((u) => u !== group));
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
        addGroup={addGroup}
        reloadFetchGroups={reloadFetchGroups}
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
              )) as ReactNode,
          ],
          // Group list
          [
            () => filteredAndSortedGroups.length > 0,
            () =>
              filteredAndSortedGroups.map((group) => (
                <ListItem
                  key={group.id}
                  secondaryAction={
                    groupsInLoading.includes(group) ? (
                      <Box sx={{ display: "flex" }}>
                        <CircularProgress color="inherit" size={25} />
                      </Box>
                    ) : (
                      <>
                        <IconButton onClick={() => setGroupToEdit(group)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          edge="end"
                          onClick={() => setGroupToDelete(group)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </>
                    )
                  }
                  disablePadding
                >
                  <ListItemButton onClick={() => setGroupToEdit(group)}>
                    <ListItemIcon>
                      <GroupIcon />
                    </ListItemIcon>
                    <ListItemText primary={group.name} />
                  </ListItemButton>
                </ListItem>
              )),
          ],
          // No group
          [
            R.T,
            () => (
              <Typography sx={{ m: 2 }} align="center">
                {t("settings.noGroup")}
              </Typography>
            ),
          ],
        ])()}
      </List>
      {groupToDelete && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setGroupToDelete(undefined)}
          onConfirm={handleDeleteGroup}
          alert="warning"
          open
        >
          {t("settings.question.deleteGroup", [groupToDelete.name])}
        </ConfirmationDialog>
      )}
      {groupToEdit && (
        <UpdateGroupDialog
          open
          group={groupToEdit}
          editGroup={editGroup}
          reloadFetchGroups={reloadFetchGroups}
          closeDialog={() => setGroupToEdit(undefined)}
        />
      )}
    </Box>
  );
}

export default Groups;
