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

import { TextField, IconButton, InputAdornment, type TextFieldProps } from "@mui/material";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";
import { useState } from "react";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";

export type PasswordFEProps = {
  value?: string;
  defaultValue?: string;
  autoComplete?: "new-password" | "current-password"; // https://web.dev/sign-in-form-best-practices/#current-password
} & Omit<TextFieldProps, "type" | "value" | "defaultValue">;

function PasswordFE({ autoComplete = "new-password", ...rest }: PasswordFEProps) {
  const [showPassword, setShowPassword] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClickShowPassword = () => setShowPassword((show) => !show);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TextField
      {...rest}
      type={showPassword ? "text" : "password"}
      autoComplete={autoComplete}
      slotProps={{
        ...rest.slotProps,
        input: {
          ...rest.slotProps?.input,
          endAdornment: (
            <InputAdornment position="end">
              <IconButton onClick={handleClickShowPassword} edge="end">
                {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
              </IconButton>
            </InputAdornment>
          ),
        },
      }}
    />
  );
}

export default reactHookFormSupport({ defaultValue: "" })(PasswordFE);
