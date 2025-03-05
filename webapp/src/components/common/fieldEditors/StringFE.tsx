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

import { TextField, type TextFieldProps } from "@mui/material";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

export interface StringFEProps extends Omit<TextFieldProps, "type" | "value" | "defaultValue"> {
  value?: string;
  defaultValue?: string;
}

function StringFE(props: StringFEProps) {
  return <TextField {...props} type="text" />;
}

export default reactHookFormSupport({ defaultValue: "" })(StringFE);
