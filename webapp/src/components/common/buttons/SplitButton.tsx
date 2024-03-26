import Button from "@mui/material/Button";
import ButtonGroup, { ButtonGroupProps } from "@mui/material/ButtonGroup";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ClickAwayListener from "@mui/material/ClickAwayListener";
import Grow from "@mui/material/Grow";
import Paper from "@mui/material/Paper";
import Popper from "@mui/material/Popper";
import MenuItem from "@mui/material/MenuItem";
import MenuList from "@mui/material/MenuList";
import * as RA from "ramda-adjunct";
import { useRef, useState } from "react";
import LoadingButton, { type LoadingButtonProps } from "@mui/lab/LoadingButton";

interface OptionObj<TOptionValue extends string = string> {
  value: TOptionValue;
  label?: string;
  disabled?: boolean;
}

export interface SlitButtonProps<TOptionValue extends string = string>
  extends Omit<ButtonGroupProps, "onClick"> {
  options: Array<TOptionValue | OptionObj<TOptionValue>>;
  dropdownActionMode?: "change" | "trigger";
  onClick?: (optionValue: TOptionValue, optionIndex: number) => void;
  ButtonProps?: Omit<LoadingButtonProps, "onClick">;
}

function formatOptions<TOptionValue extends string>(
  options: SlitButtonProps<TOptionValue>["options"],
) {
  return options.map((option) =>
    RA.isString(option) ? { value: option } : option,
  );
}

export default function SplitButton<TOptionValue extends string>(
  props: SlitButtonProps<TOptionValue>,
) {
  const {
    options,
    dropdownActionMode = "trigger",
    onClick,
    children,
    ButtonProps: loadingButtonProps,
    ...buttonGroupProps
  } = props;
  const [open, setOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const anchorRef = useRef<HTMLDivElement>(null);
  const formattedOptions = formatOptions(options);
  const isChangeMode = dropdownActionMode === "change";
  const isTriggerMode = dropdownActionMode === "trigger";

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleButtonClick = () => {
    if (!onClick || formattedOptions.length === 0) {
      return;
    }

    if (isChangeMode) {
      const { value } = formattedOptions[selectedIndex];
      onClick(value, selectedIndex);
      return;
    }

    onClick(formattedOptions[0].value, 0);
  };

  const handleMenuItemClick = (
    event: React.MouseEvent<HTMLLIElement, MouseEvent>,
    index: number,
  ) => {
    setSelectedIndex(index);
    setOpen(false);

    if (isTriggerMode) {
      const { value } = formattedOptions[index];
      onClick?.(value, index);
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
      <ButtonGroup {...buttonGroupProps} ref={anchorRef}>
        <LoadingButton
          variant={buttonGroupProps.variant || "outlined"} // `LoadingButton` doesn't inherit from `ButtonGroup`
          {...loadingButtonProps}
          onClick={handleButtonClick}
        >
          {getButtonLabel(selectedIndex)}
        </LoadingButton>
        <Button
          size="small"
          onClick={handleToggle}
          disabled={buttonGroupProps.disabled || loadingButtonProps?.loading}
        >
          <ArrowDropDownIcon />
        </Button>
      </ButtonGroup>
      <Popper
        sx={{ zIndex: 1000 }}
        open={open}
        anchorEl={anchorRef.current}
        role={undefined}
        transition
        disablePortal
      >
        {({ TransitionProps, placement }) => (
          <Grow
            {...TransitionProps}
            style={{
              transformOrigin:
                placement === "bottom" ? "center top" : "center bottom",
            }}
          >
            <Paper>
              <ClickAwayListener onClickAway={handleClose}>
                <MenuList autoFocusItem>
                  {formattedOptions.map((option, index) => (
                    <MenuItem
                      key={option.value}
                      disabled={option.disabled}
                      selected={isChangeMode && index === selectedIndex}
                      onClick={(event) => handleMenuItemClick(event, index)}
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
