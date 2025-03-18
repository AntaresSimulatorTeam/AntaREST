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

import TokenIcon from "@mui/icons-material/Token";
import { IconButton, Paper, Tooltip } from "@mui/material";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import type { BotCreateDTO, BotDTO, GroupDTO, RoleType } from "../../../../../types/types";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import { createBot } from "../../../../../services/api/user";
import OkDialog from "../../../../common/dialogs/OkDialog";
import TokenFormDialog, { type TokenFormDialogProps } from "./TokenFormDialog";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";

type InheritPropsToOmit = "title" | "titleIcon" | "onSubmit" | "onCancel";

interface Props extends Omit<TokenFormDialogProps, InheritPropsToOmit> {
  addToken: (token: BotDTO) => void;
  reloadFetchTokens: VoidFunction;
  closeDialog: VoidFunction;
}

function CreateTokenDialog(props: Props) {
  const { addToken, reloadFetchTokens, closeDialog, ...dialogProps } = props;
  const [tokenValueToDisplay, setTokenValueToDisplay] = useState("");
  const [showCopiedTooltip, setShowCopiedTooltip] = useState(false);
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus) => {
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
      closeDialog();
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
        title={t("settings.createToken")}
        titleIcon={TokenIcon}
        onSubmit={handleSubmit}
        onCancel={closeDialog}
        {...dialogProps}
      />
      {tokenValueToDisplay && (
        <OkDialog
          open
          title={t("settings.message.printToken") as string}
          onOk={() => {
            setTokenValueToDisplay("");
            closeDialog();
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
                PopperProps={{
                  disablePortal: true,
                }}
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
