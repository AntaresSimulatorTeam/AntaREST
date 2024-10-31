/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useMemo } from "react";
import { FieldValues } from "react-hook-form";
import { useTranslation } from "react-i18next";

import { Info } from "@mui/icons-material";
import { DialogContentText } from "@mui/material";

import { BotDetailsDTO } from "@/common/types";
import OkDialog, { OkDialogProps } from "@/components/common/dialogs/OkDialog";
import Form from "@/components/common/Form";

import TokenForm from "./TokenFormDialog/TokenForm";

interface Props extends Omit<OkDialogProps, "title" | "titleIcon"> {
  token: BotDetailsDTO;
}

function TokenInfoDialog(props: Props) {
  const { token, ...dialogProps } = props;

  // TODO: FieldValues is used to fix an issue with TokenForm
  const defaultValues = useMemo<FieldValues>(
    () => ({
      name: token.name,
      permissions: token.roles.map((role) => ({
        group: {
          id: role.group_id,
          name: role.group_name,
        },
        type: role.type,
      })),
    }),
    [token],
  );

  const { t } = useTranslation();

  return (
    <OkDialog
      maxWidth="sm"
      fullWidth
      {...dialogProps}
      title={t("global.permissions")}
      titleIcon={Info}
    >
      <DialogContentText>
        {t("settings.currentToken", { 0: token.name })}
      </DialogContentText>
      <Form config={{ defaultValues }} hideSubmitButton>
        {(formObj) => <TokenForm onlyPermissions readOnly {...formObj} />}
      </Form>
    </OkDialog>
  );
}

export default TokenInfoDialog;
