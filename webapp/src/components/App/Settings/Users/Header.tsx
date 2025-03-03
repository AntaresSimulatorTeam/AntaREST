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

import { Box, Button } from "@mui/material";
import PersonAddAltIcon from "@mui/icons-material/PersonAddAlt";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import CreateUserDialog from "./dialog/CreateUserDialog";
import type { UserDetailsDTO } from "../../../../types/types";
import SearchFE from "../../../common/fieldEditors/SearchFE";

interface Props {
  setSearchValue: (v: string) => void;
  addUser: (user: UserDetailsDTO) => void;
  reloadFetchUsers: () => void;
}

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
        <SearchFE sx={{ m: 0 }} onSearchValueChange={setSearchValue} />
        <Button
          startIcon={<PersonAddAltIcon />}
          variant="outlined"
          onClick={() => setShowCreateUserModal(true)}
        >
          {t("global.create")}
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
