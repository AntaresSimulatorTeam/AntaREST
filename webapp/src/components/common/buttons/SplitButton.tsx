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

import { useRef, useState } from "react";
import {
  Button,
  ButtonGroup,
  ClickAwayListener,
  Grow,
  Paper,
  Popper,
  MenuItem,
  MenuList,
  type ButtonGroupProps,
  type ButtonProps,
} from "@mui/material";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";

interface OptionObj<Value extends string = string> {
  value: Value;
  label?: string;
  disabled?: boolean;
}

export interface SplitButtonProps<OptionValue extends string = string>
  extends Omit<ButtonGroupProps, "onClick"> {
  options: Array<OptionValue | OptionObj<OptionValue>>;
  dropdownActionMode?: "change" | "trigger";
  onClick?: (optionValue: OptionValue, optionIndex: number) => void;
  ButtonProps?: Omit<ButtonProps, "onClick">;
}

export default function SplitButton<OptionValue extends string>(
  props: SplitButtonProps<OptionValue>,
) {
  const {
    options,
    dropdownActionMode = "trigger",
    onClick,
    children,
    ButtonProps,
    disabled,
    ...buttonGroupProps
  } = props;
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
    return label ?? value;
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
        <Button
          variant={buttonGroupProps.variant || "outlined"} // `LoadingButton` doesn't inherit from `ButtonGroup`
          {...ButtonProps}
          onClick={handleButtonClick}
        >
          {getButtonLabel(selectedIndex)}
        </Button>
        <Button onClick={handleToggle} disabled={disabled || !!ButtonProps?.loading}>
          <ArrowDropDownIcon />
        </Button>
      </ButtonGroup>
      <Popper
        sx={{ zIndex: 1000 }}
        open={open}
        anchorEl={anchorRef.current}
        transition
        disablePortal
      >
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
