/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { TREE_ROOT_NAME } from "@/components/utils/constants";
import reactHookFormSupport from "@/hoc/reactHookFormSupport";
import { validatePath, validateString } from "@/utils/validation/string";
import { combineValidators } from "@/utils/validation/utils";
import { InputAdornment, TextField, type TextFieldProps } from "@mui/material";
import { useTranslation } from "react-i18next";

interface Props extends Omit<TextFieldProps, "type" | "value" | "defaultValue" | "label"> {
  value?: string;
  defaultValue?: string;
  disableAdornment?: boolean;
}

function StudyPathFE({ slotProps, helperText, disableAdornment = false, ...rest }: Props) {
  const { t } = useTranslation();

  return (
    <TextField
      {...rest}
      type="text"
      label={t("global.folder")}
      slotProps={{
        ...slotProps,
        input: {
          ...slotProps?.input,
          startAdornment: disableAdornment ? undefined : (
            <InputAdornment position="start">{`${TREE_ROOT_NAME}/`}</InputAdornment>
          ),
        },
      }}
      helperText={helperText ?? t("form.field.path.help")}
    />
  );
}

const StudyPathFEWithReactHookFormSupport = reactHookFormSupport({
  defaultValue: "",
  preValidate: combineValidators(
    // Default workspace is set if empty
    validatePath({
      allowEmpty: true,
      allowToStartWithSlash: false,
    }),
    validateString({
      specialChars: { chars: "=", mode: "deny" },
      allowEmpty: true,
    }),
  ),
})(StudyPathFE);

export default StudyPathFEWithReactHookFormSupport;
