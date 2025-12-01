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

import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import useConfirm from "@/hooks/useConfirm";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { deleteBot } from "@/services/api/user";
import { sortByName } from "@/services/utils";
import type { BotDetailsDTO } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { isSearchMatching } from "@/utils/stringUtils";
import DeleteIcon from "@mui/icons-material/Delete";
import InfoIcon from "@mui/icons-material/Info";
import TokenIcon from "@mui/icons-material/Token";
import {
  Box,
  CircularProgress,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import ReadTokenDialog from "./dialog/ReadTokenDialog";
import type { BotDetailsDtoWithUser } from "./types";

interface Props {
  tokens: BotDetailsDtoWithUser[];
  searchValue: string;
  setTokensInLoading: React.Dispatch<React.SetStateAction<Array<BotDetailsDTO["id"]>>>;
  tokensInLoading: Array<BotDetailsDTO["id"]>;
  reloadFetchTokens: VoidFunction;
}

function TokenList({
  tokens,
  searchValue,
  setTokensInLoading,
  tokensInLoading,
  reloadFetchTokens,
}: Props) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [tokenToDisplayInfo, setTokenToDisplayInfo] = useState<BotDetailsDTO>();
  const deleteAction = useConfirm<{ tokenName: string }>();

  const filteredAndSortedTokens = useMemo(() => {
    const filteredTokens = searchValue
      ? tokens.filter(({ name, user }) => isSearchMatching(searchValue, [name, user?.name || ""]))
      : tokens;

    return sortByName(filteredTokens);
  }, [searchValue, tokens]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDeleteToken = async (token: BotDetailsDtoWithUser) => {
    const tokenName = token.name;
    const confirm = await deleteAction.showConfirm({ data: { tokenName } });

    if (!confirm) {
      return;
    }

    setTokensInLoading((prev) => [...prev, token.id]);

    try {
      await deleteBot(token.id);

      enqueueSnackbar(t("settings.success.tokenDelete", { 0: tokenName }), {
        variant: "success",
      });

      reloadFetchTokens();
    } catch (err) {
      enqueueErrorSnackbar(t("settings.error.tokenDelete", { 0: tokenName }), toError(err));
    } finally {
      setTokensInLoading((prev) => prev.filter((id) => id !== token.id));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (filteredAndSortedTokens.length === 0) {
    return (
      <Typography sx={{ m: 2 }} align="center">
        {t("settings.noToken")}
      </Typography>
    );
  }

  return (
    <>
      {filteredAndSortedTokens.map((token) => (
        <ListItem
          key={token.id}
          secondaryAction={
            tokensInLoading.includes(token.id) ? (
              <Box sx={{ display: "flex" }}>
                <CircularProgress color="secondary" size={25} />
              </Box>
            ) : (
              <>
                <IconButton onClick={() => setTokenToDisplayInfo(token)}>
                  <InfoIcon />
                </IconButton>
                <IconButton edge="end" onClick={() => handleDeleteToken(token)}>
                  <DeleteIcon />
                </IconButton>
              </>
            )
          }
          disablePadding
        >
          <ListItemButton onClick={() => setTokenToDisplayInfo(token)}>
            <ListItemIcon>
              <TokenIcon />
            </ListItemIcon>
            <ListItemText
              primary={
                <Box sx={{ display: "flex" }}>
                  {token.name}
                  <Typography sx={{ ml: 2, opacity: 0.4, fontStyle: "italic" }}>
                    {token.user?.name || ""}
                  </Typography>
                </Box>
              }
            />
          </ListItemButton>
        </ListItem>
      ))}
      <ConfirmationDialog
        open={deleteAction.isPending}
        titleIcon={DeleteIcon}
        onCancel={deleteAction.no}
        onConfirm={deleteAction.yes}
        alert="warning"
      >
        {t("settings.question.deleteToken", { 0: deleteAction.data?.tokenName })}
      </ConfirmationDialog>
      {tokenToDisplayInfo && (
        <ReadTokenDialog
          open
          onCancel={() => setTokenToDisplayInfo(undefined)}
          token={tokenToDisplayInfo}
        />
      )}
    </>
  );
}

export default TokenList;
