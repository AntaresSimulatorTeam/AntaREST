import { Box, Button, InputAdornment, TextField } from "@mui/material";
import TokenIcon from "@mui/icons-material/Token";
import { useTranslation } from "react-i18next";
import SearchIcon from "@mui/icons-material/Search";
import { useState } from "react";
import { BotDTO } from "../../../common/types";
import CreateTokenDialog from "./dialog/CreateTokenDialog";

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
          startIcon={<TokenIcon />}
          variant="outlined"
          onClick={() => setShowCreateTokenModal(true)}
        >
          {t("main:create")}
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
