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
import TokenIcon from "@mui/icons-material/Token";
import { IconButton, Paper } from "@mui/material";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { createBot } from "../../../../../services/api/user";
import type { BotCreateDTO, GroupDTO, RoleType } from "../../../../../types/types";
import OkDialog from "../../../../common/dialogs/OkDialog";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";
import TokenFormDialog from "./TokenFormDialog";
import type { TokenFormDefaultValues } from "./utils";

interface Props {
  open: boolean;
  onCancel: VoidFunction;
  reloadFetchTokens: VoidFunction;
}

function CreateTokenDialog({ open, reloadFetchTokens, onCancel }: Props) {
  const [tokenValueToDisplay, setTokenValueToDisplay] = useState("");
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<TokenFormDefaultValues>) => {
    const { name, permissions } = data.values;

    const roles = permissions.map((perm: { group: GroupDTO; type: RoleType }) => ({
      group: perm.group.id,
      role: perm.type,
    })) as BotCreateDTO["roles"];

    return createBot({ name, is_author: false, roles });
  };

  const handleSubmitSuccessful = (
    data: SubmitHandlerPlus<TokenFormDefaultValues>,
    tokenValue: string,
  ) => {
    setTokenValueToDisplay(tokenValue);
    reloadFetchTokens();
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(tokenValueToDisplay);
    enqueueSnackbar(t("global.copied"), { variant: "success" });
  };

  const handleOk = () => {
    setTokenValueToDisplay("");
    onCancel();
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
        onSubmitSuccessful={handleSubmitSuccessful}
        onCancel={onCancel}
        submitButtonIcon={<TokenIcon />}
        submitButtonText={t("global.create")}
      />
      <OkDialog
        open={!!tokenValueToDisplay}
        title={t("settings.message.printToken") as string}
        onOk={handleOk}
      >
        <Paper
          sx={{
            p: 2,
            pb: 6,
            position: "relative",
            overflowWrap: "break-word",
          }}
        >
          {tokenValueToDisplay}
          <IconButton onClick={handleCopy} sx={{ position: "absolute", right: 3, bottom: 3 }}>
            <ContentCopyIcon />
          </IconButton>
        </Paper>
      </OkDialog>
    </>
  );
}

export default CreateTokenDialog;
