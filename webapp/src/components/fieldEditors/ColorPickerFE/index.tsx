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

import { Box, TextField, InputAdornment, type TextFieldProps } from "@mui/material";
import { useRef, useState } from "react";
import { SketchPicker, type ColorResult } from "react-color";
import SquareRoundedIcon from "@mui/icons-material/SquareRounded";
import { useClickAway, useKey, useUpdateEffect } from "react-use";
import { rgbToString, stringToRGB } from "./utils";
import { mergeSxProp } from "../../../../utils/muiUtils";
import { composeRefs } from "../../../../utils/reactUtils";
import reactHookFormSupport from "../../../../hoc/reactHookFormSupport";

export type ColorPickerFEProps = Omit<TextFieldProps, "type" | "defaultChecked"> & {
  value?: string; // Format: R,G,B - ex: "255,255,255"
  defaultValue?: string;
};

function ColorPickerFE(props: ColorPickerFEProps) {
  const { value, defaultValue, onChange, sx, inputRef, ...textFieldProps } = props;
  const [currentColor, setCurrentColor] = useState(defaultValue || value || "");
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const internalRef = useRef<HTMLInputElement>();
  const pickerWrapperRef = useRef(null);

  useUpdateEffect(() => {
    setCurrentColor(value ?? "");
  }, [value]);

  useClickAway(pickerWrapperRef, () => {
    setIsPickerOpen(false);
  });

  useKey("Escape", () => setIsPickerOpen(false));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = ({ hex, rgb }: ColorResult) => {
    setCurrentColor(["transparent", "#0000"].includes(hex) ? "" : rgbToString(rgb));
  };

  const handleChangeComplete = () => {
    onChange?.({
      target: internalRef.current,
      type: "change",
    } as React.ChangeEvent<HTMLInputElement>);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={mergeSxProp(
        {
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          position: "relative",
        },
        sx,
      )}
    >
      <TextField
        {...textFieldProps}
        value={currentColor}
        placeholder={currentColor}
        inputRef={composeRefs(inputRef, internalRef)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SquareRoundedIcon
                sx={{
                  color: currentColor ? `rgb(${currentColor})` : "transparent",
                }}
              />
            </InputAdornment>
          ),
        }}
        onClick={() => setIsPickerOpen(true)}
      />
      {isPickerOpen && (
        <Box
          sx={{
            position: "absolute",
            top: "calc(95%)",
            zIndex: 1000,
          }}
          ref={pickerWrapperRef}
        >
          <SketchPicker
            color={currentColor && stringToRGB(currentColor)}
            onChange={handleChange}
            onChangeComplete={handleChangeComplete}
            disableAlpha
          />
        </Box>
      )}
    </Box>
  );
}

export default reactHookFormSupport({ defaultValue: "" })(ColorPickerFE);
