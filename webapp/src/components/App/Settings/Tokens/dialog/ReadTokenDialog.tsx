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

import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { BotDetailsDTO } from "../../../../../types/types";
import TokenFormDialog from "./TokenFormDialog";
import type { TokenFormDefaultValues } from "./utils";

interface Props {
  open: boolean;
  onCancel: VoidFunction;
  token: BotDetailsDTO;
}

function ReadTokenDialog({ open, onCancel, token }: Props) {
  const { t } = useTranslation();

  const defaultValues = useMemo<TokenFormDefaultValues>(
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TokenFormDialog
      open={open}
      title={t("global.permissions")}
      config={{ defaultValues }}
      onCancel={onCancel}
      readOnly
    />
  );
}

export default ReadTokenDialog;
