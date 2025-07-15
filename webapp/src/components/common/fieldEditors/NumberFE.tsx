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

import { setValueAsNumber } from "@/utils/reactHookFormUtils";
import { TextField, type TextFieldProps } from "@mui/material";
import * as RA from "ramda-adjunct";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

export interface NumberFEProps extends Omit<TextFieldProps, "type" | "value" | "defaultValue"> {
  value?: number;
  defaultValue?: number;
}

function NumberFE(props: NumberFEProps) {
  return <TextField {...props} type="number" />;
}

export default reactHookFormSupport({
  defaultValue: "" as unknown as number,
  setValueAs: setValueAsNumber,
  preValidate: RA.isNumber,
})(NumberFE);
