import { Box, Button, InputAdornment, TextField } from "@mui/material";
import PersonAddAltIcon from "@mui/icons-material/PersonAddAlt";
import { useTranslation } from "react-i18next";
import SearchIcon from "@mui/icons-material/Search";
import { useState } from "react";
import CreateUserDialog from "./dialog/CreateUserDialog";
import { UserDetailsDTO } from "../../../common/types";

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

  return (
    <>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: "5px",
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
          onChange={(event) => setSearchValue(event.target.value)}
        />
        <Button
          startIcon={<PersonAddAltIcon />}
          variant="outlined"
          onClick={() => setShowCreateUserModal(true)}
        >
          {t("main:create")}
        </Button>
      </Box>
      {showCreateUserModal && (
        <CreateUserDialog
          open
          addUser={addUser}
          reloadFetchUsers={reloadFetchUsers}
          closeDialog={() => setShowCreateUserModal(false)}
        />
      )}
    </>
  );
}

export default Header;
