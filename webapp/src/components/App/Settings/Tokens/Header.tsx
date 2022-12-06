import { Box, Button } from "@mui/material";
import TokenIcon from "@mui/icons-material/Token";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import { BotDTO } from "../../../../common/types";
import CreateTokenDialog from "./dialog/CreateTokenDialog";
import SearchFE from "../../../common/fieldEditors/SearchFE";

/**
 * Types
 */

interface Props {
  setSearchValue: (v: string) => void;
  addToken: (user: BotDTO) => void;
  reloadFetchTokens: () => void;
}

/**
 * Component
 */

function Header(props: Props) {
  const { setSearchValue, addToken, reloadFetchTokens } = props;
  const { t } = useTranslation();
  const [showCreateTokenModal, setShowCreateTokenModal] = useState(false);

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
          startIcon={<TokenIcon />}
          variant="outlined"
          onClick={() => setShowCreateTokenModal(true)}
        >
          {t("global.create")}
        </Button>
      </Box>
      {showCreateTokenModal && (
        <CreateTokenDialog
          open
          addToken={addToken}
          reloadFetchTokens={reloadFetchTokens}
          closeDialog={() => setShowCreateTokenModal(false)}
        />
      )}
    </>
  );
}

export default Header;
