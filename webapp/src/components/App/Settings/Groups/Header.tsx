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
import GroupAddIcon from "@mui/icons-material/GroupAdd";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import type { GroupDetailsDTO } from "../../../../types/types";
import CreateGroupDialog from "./dialog/CreateGroupDialog";
import { isAuthUserAdmin } from "../../../../redux/selectors";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import SearchFE from "../../../common/fieldEditors/SearchFE";

interface Props {
  setSearchValue: (v: string) => void;
  addGroup: (user: GroupDetailsDTO) => void;
  reloadFetchGroups: () => void;
}

function Header(props: Props) {
  const { setSearchValue, addGroup, reloadFetchGroups } = props;
  const { t } = useTranslation();
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const isUserAdmin = useAppSelector(isAuthUserAdmin);

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
        {isUserAdmin && (
          <Button
            startIcon={<GroupAddIcon />}
            variant="outlined"
            onClick={() => setShowCreateGroupModal(true)}
          >
            {t("global.create")}
          </Button>
        )}
      </Box>
      {showCreateGroupModal && (
        <CreateGroupDialog
          open
          addGroup={addGroup}
          reloadFetchGroups={reloadFetchGroups}
          closeDialog={() => setShowCreateGroupModal(false)}
        />
      )}
    </>
  );
}

export default Header;
