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

import { Box, Tooltip, type ButtonProps, type TextFieldProps } from "@mui/material";
import { cloneElement } from "react";

export interface FieldEditorButtonGroupProps {
  children: [
    React.ReactElement<Pick<TextFieldProps, "slotProps" | "size">>,
    React.ReactElement<Pick<ButtonProps, "variant" | "size" | "sx">>,
  ];
  size?: TextFieldProps["size"];
  tooltip?: React.ReactNode;
}

function FieldEditorButtonGroup({ children, size, tooltip }: FieldEditorButtonGroupProps) {
  const [fieldEditor, button] = children;

  const fieldEditorCloned = cloneElement(fieldEditor, {
    slotProps: {
      input: {
        sx: {
          borderTopRightRadius: 0,
          borderBottomRightRadius: 0,
        },
      },
    },
    size,
  });

  const buttonCloned = cloneElement(button, {
    variant: "contained",
    sx: [
      {
        borderTopLeftRadius: 0,
        borderBottomLeftRadius: 0,
      },
      !!tooltip && { height: 1 },
    ],
    size,
  });

  return (
    <Box sx={{ display: "flex" }}>
      {fieldEditorCloned}
      {tooltip ? (
        <Tooltip title={tooltip}>
          <span>{buttonCloned}</span>
        </Tooltip>
      ) : (
        buttonCloned
      )}
    </Box>
  );
}

export default FieldEditorButtonGroup;
