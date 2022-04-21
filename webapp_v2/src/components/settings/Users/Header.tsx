import { Box, Button, InputAdornment, TextField } from "@mui/material";
import PersonAddAltIcon from "@mui/icons-material/PersonAddAlt";
import { useTranslation } from "react-i18next";
import SearchIcon from "@mui/icons-material/Search";
import { ChangeEvent, useState } from "react";
import { FieldValues, UnpackNestedValue } from "react-hook-form";
import { usePromise as usePromiseWrapper } from "react-use";
import { useSnackbar } from "notistack";
import CreateUserDialog from "./CreateUserDialog";
import { createRole, createUser } from "../../../services/api/user";
import {
  GroupDTO,
  RoleCreationReturnDTO,
  UserDetailsDTO,
  UserDTO,
} from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";

/**
 * Types
 */

interface Props {
  setSearchValue: (v: string) => void;
  addUser: (user: UserDetailsDTO) => void;
  reloadFetchUsers: () => void;
}

/**
 * Component
 */

function Header(props: Props) {
  const { setSearchValue, addUser, reloadFetchUsers } = props;
  const { t } = useTranslation();
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSearchValue(event.target.value);
  };

  const handleCreateUserClick = () => {
    setShowCreateUserModal(true);
  };

  const handleCreateUser = async (data: UnpackNestedValue<FieldValues>) => {
    const { username, password, permissions } = data;
    let newUser: UserDTO;

    try {
      newUser = await mounted(createUser(username, password));
      enqueueSnackbar(t("settings:onUserCreation", { user: newUser }), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(
        t("settings:onUserSaveError", { name: username }),
        e as Error
      );
      throw e;
    }

    try {
      const promises = permissions.map(
        (perm: { group: GroupDTO; type: number }) =>
          createRole({
            group_id: perm.group.id,
            type: perm.type,
            identity_id: newUser.id,
          })
      );

      const res: RoleCreationReturnDTO[] = await mounted(Promise.all(promises));

      const roles: UserDetailsDTO["roles"] = res.map(
        ({ group, identity, type }) => ({
          group_id: group.id,
          group_name: group.name,
          identity_id: identity.id,
          type,
        })
      );

      addUser({ ...newUser, roles });
    } catch (e) {
      // Because we cannot recover roles eventually created
      reloadFetchUsers();

      enqueueErrorSnackbar(
        t("settings:onUserRolesSaveError", { name: username }),
        e as Error
      );
    }

    setShowCreateUserModal(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <TextField
          sx={{ m: 0 }}
          placeholder={t("main:search")}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          onChange={handleSearchChange}
        />
        <Button
          startIcon={<PersonAddAltIcon />}
          variant="outlined"
          onClick={handleCreateUserClick}
        >
          {t("settings:newUserTitle")}
        </Button>
      </Box>
      {showCreateUserModal && (
        <CreateUserDialog
          open
          onSubmit={handleCreateUser}
          onCancel={() => setShowCreateUserModal(false)}
        />
      )}
    </>
  );
}

export default Header;
