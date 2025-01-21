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

import { TextField, type TextFieldProps } from "@mui/material";
import * as RA from "ramda-adjunct";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

export type NumberFEProps = {
  value?: number;
  defaultValue?: number;
} & Omit<TextFieldProps, "type" | "value" | "defaultValue">;

function NumberFE(props: NumberFEProps) {
  return <TextField {...props} type="number" />;
}

export default reactHookFormSupport({
  defaultValue: "" as unknown as number,
  // Returning empty string allow to type negative number
  setValueAs: (v) => (v === "" ? "" : Number(v)),
  preValidate: RA.isNumber,
})(NumberFE);
