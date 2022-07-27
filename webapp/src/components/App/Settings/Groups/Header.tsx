import { Box, Button } from "@mui/material";
import GroupAddIcon from "@mui/icons-material/GroupAdd";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import { GroupDetailsDTO } from "../../../../common/types";
import CreateGroupDialog from "./dialog/CreateGroupDialog";
import { isAuthUserAdmin } from "../../../../redux/selectors";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import SearchFE from "../../../common/fieldEditors/SearchFE";

/**
 * Types
 */

interface Props {
  setSearchValue: (v: string) => void;
  addGroup: (user: GroupDetailsDTO) => void;
  reloadFetchGroups: () => void;
}

/**
 * Component
 */

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
        <SearchFE sx={{ m: 0 }} setSearchValue={setSearchValue} />
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
