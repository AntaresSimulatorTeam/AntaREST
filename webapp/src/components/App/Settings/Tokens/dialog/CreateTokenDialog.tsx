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

import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { IconButton, Paper, Tooltip } from "@mui/material";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import { createBot } from "../../../../../services/api/user";
import type { BotCreateDTO, BotDTO, GroupDTO, RoleType } from "../../../../../types/types";
import OkDialog from "../../../../common/dialogs/OkDialog";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";
import TokenFormDialog from "./TokenFormDialog";
import type { TokenFormDefaultValues } from "./utils";

interface Props {
  open: boolean;
  onCancel: VoidFunction;
  addToken: (token: BotDTO) => void;
  reloadFetchTokens: VoidFunction;
}

function CreateTokenDialog({ open, addToken, reloadFetchTokens, onCancel }: Props) {
  const [tokenValueToDisplay, setTokenValueToDisplay] = useState("");
  const [showCopiedTooltip, setShowCopiedTooltip] = useState(false);
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<TokenFormDefaultValues>) => {
    const { name, permissions } = data.values;

    try {
      const roles = permissions.map((perm: { group: GroupDTO; type: RoleType }) => ({
        group: perm.group.id,
        role: perm.type,
      })) as BotCreateDTO["roles"];

      const tokenValue = await mounted(createBot({ name, is_author: false, roles }));

      setTokenValueToDisplay(tokenValue);

      enqueueSnackbar(t("settings.success.tokenCreation", { 0: name }), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("settings.error.tokenSave", { 0: name }), e as Error);
      onCancel();
    } finally {
      reloadFetchTokens();
    }
  };

  const handleCopyClick = () => {
    navigator.clipboard.writeText(tokenValueToDisplay).then(() => setShowCopiedTooltip(true));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <TokenFormDialog
        open={open}
        title={t("settings.createToken")}
        onSubmit={handleSubmit}
        onCancel={onCancel}
      />
      {tokenValueToDisplay && (
        <OkDialog
          open
          title={t("settings.message.printToken") as string}
          onOk={() => {
            setTokenValueToDisplay("");
            onCancel();
          }}
        >
          <Paper
            sx={{
              p: 2,
              pb: 6,
              position: "relative",
              overflowWrap: "break-word",
              backgroundImage:
                "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
            }}
          >
            {tokenValueToDisplay}
            <IconButton sx={{ position: "absolute", right: 3, bottom: 3 }} size="large">
              <Tooltip
                open={showCopiedTooltip}
                slotProps={{ popper: { disablePortal: true } }}
                onClose={() => setShowCopiedTooltip(false)}
                disableFocusListener
                disableHoverListener
                disableTouchListener
                title={t("global.copied") as string}
              >
                <ContentCopyIcon onClick={handleCopyClick} />
              </Tooltip>
            </IconButton>
          </Paper>
        </OkDialog>
      )}
    </>
  );
}

export default CreateTokenDialog;
