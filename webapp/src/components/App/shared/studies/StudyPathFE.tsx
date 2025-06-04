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

import StringFE, { type StringFEProps } from "@/components/common/fieldEditors/StringFE";
import { DEFAULT_WORKSPACE_NAME } from "@/components/common/utils/constants";
import reactHookFormSupport from "@/hoc/reactHookFormSupport";
import { validatePath } from "@/utils/validation/string";
import { InputAdornment } from "@mui/material";
import { useTranslation } from "react-i18next";

type Props = Omit<StringFEProps, "label" | "name">;

function StudyPathFE(props: Props) {
  const { t } = useTranslation();

  return (
    <StringFE
      {...props}
      label={t("global.folder")}
      slotProps={{
        input: {
          startAdornment: (
            <InputAdornment position="start">{`${DEFAULT_WORKSPACE_NAME}/`}</InputAdornment>
          ),
        },
      }}
      helperText={props.helperText ?? t("form.field.path.help")}
    />
  );
}

const StudyPathFEWithReactHookFormSupport = reactHookFormSupport({
  defaultValue: "",
  preValidate: validatePath({
    allowEmpty: true,
    allowToStartWithSlash: false,
  }),
})(StudyPathFE);

export default StudyPathFEWithReactHookFormSupport;
