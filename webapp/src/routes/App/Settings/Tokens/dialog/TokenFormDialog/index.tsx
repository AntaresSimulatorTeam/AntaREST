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
import FormDialog, { type FormDialogProps } from "../../../../../common/dialogs/FormDialog";
import { TOKEN_FORM_DEFAULT_VALUES, type TokenFormDefaultValues } from "../utils";
import TokenForm from "./TokenForm";

export interface TokenFormDialogProps
  extends Omit<FormDialogProps<TokenFormDefaultValues>, "children" | "maxWidth" | "titleIcon"> {
  defaultValues?: TokenFormDefaultValues;
  readOnly?: boolean;
}

function TokenFormDialog({
  defaultValues: defaultValuesFromProps,
  readOnly,
  ...dialogProps
}: TokenFormDialogProps) {
  return (
    <FormDialog
      maxWidth="xs"
      titleIcon={TokenIcon}
      config={{ defaultValues: { ...TOKEN_FORM_DEFAULT_VALUES, ...defaultValuesFromProps } }}
      {...dialogProps}
    >
      <TokenForm readOnly={readOnly} />
    </FormDialog>
  );
}

export default TokenFormDialog;
