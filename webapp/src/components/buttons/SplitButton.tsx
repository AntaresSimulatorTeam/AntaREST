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

import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import {
  Button,
  ButtonGroup,
  ClickAwayListener,
  Grow,
  MenuItem,
  MenuList,
  Paper,
  Popper,
  type ButtonGroupProps,
  type ButtonProps,
} from "@mui/material";
import type { TFunction } from "i18next";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";

interface Option<T extends string = string> {
  value: T;
  label?: string | ((t: TFunction) => string);
  disabled?: boolean;
}

export type Options<T extends string = string> =
  | Array<T | Option<T>>
  | ReadonlyArray<T | Option<T>>;

export interface SplitButtonProps<OptionValue extends string = string>
  extends Omit<ButtonGroupProps, "onClick"> {
  options: Options<OptionValue>;
  dropdownActionMode?: "change" | "trigger";
  onClick?: (optionValue: OptionValue, optionIndex: number) => void;
  ButtonProps?: Omit<ButtonProps, "onClick">;
}

export default function SplitButton<OptionValue extends string>({
  options,
  dropdownActionMode = "trigger",
  onClick,
  children,
  ButtonProps,
  disabled,
  ...buttonGroupProps
}: SplitButtonProps<OptionValue>) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const anchorRef = useRef<HTMLDivElement>(null);
  const isChangeMode = dropdownActionMode === "change";
  const isTriggerMode = dropdownActionMode === "trigger";
  const formattedOptions = options.map((option) =>
    typeof option === "string" ? { value: option } : option,
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleButtonClick = () => {
    if (onClick && formattedOptions.length > 0) {
      const index = isChangeMode ? selectedIndex : 0;
      onClick(formattedOptions[index].value, index);
    }
  };

  const handleMenuItemClick = (index: number) => {
    setSelectedIndex(index);
    setOpen(false);

    if (isTriggerMode) {
      onClick?.(formattedOptions[index].value, index);
    }
  };

  const handleToggle = () => {
    setOpen((prevOpen) => !prevOpen);
  };

  const handleClose = (event: Event) => {
    if (anchorRef.current?.contains(event.target as HTMLElement)) {
      return;
    }

    setOpen(false);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getDropdownLabel = (index: number) => {
    const { value, label } = formattedOptions[index] || {};
    return typeof label === "function" ? label(t) : (label ?? value);
  };

  const getButtonLabel = (index: number) => {
    return isChangeMode ? getDropdownLabel(index) : children;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <ButtonGroup
        {...buttonGroupProps}
        disabled={disabled || formattedOptions.length === 0}
        ref={anchorRef}
      >
        <Button {...ButtonProps} onClick={handleButtonClick}>
          {getButtonLabel(selectedIndex)}
        </Button>
        <Button onClick={handleToggle} disabled={disabled || !!ButtonProps?.loading}>
          <ArrowDropDownIcon />
        </Button>
      </ButtonGroup>
      <Popper open={open} anchorEl={anchorRef.current} transition>
        {({ TransitionProps }) => (
          <Grow {...TransitionProps}>
            <Paper>
              <ClickAwayListener onClickAway={handleClose}>
                <MenuList autoFocusItem>
                  {formattedOptions.map((option, index) => (
                    <MenuItem
                      key={option.value}
                      disabled={option.disabled}
                      selected={isChangeMode && index === selectedIndex}
                      onClick={() => handleMenuItemClick(index)}
                    >
                      {getDropdownLabel(index)}
                    </MenuItem>
                  ))}
                </MenuList>
              </ClickAwayListener>
            </Paper>
          </Grow>
        )}
      </Popper>
    </>
  );
}
