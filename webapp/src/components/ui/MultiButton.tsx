import React from 'react';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import ButtonGroup from '@material-ui/core/ButtonGroup';
import ArrowDropDownIcon from '@material-ui/icons/ArrowDropDown';
import ClickAwayListener from '@material-ui/core/ClickAwayListener';
import Grow from '@material-ui/core/Grow';
import Paper from '@material-ui/core/Paper';
import Popper from '@material-ui/core/Popper';
import MenuItem from '@material-ui/core/MenuItem';
import MenuList from '@material-ui/core/MenuList';
import { useTranslation } from 'react-i18next';
import { makeStyles } from '@material-ui/core';

const useStyles = makeStyles({
  root: {},
  button: {},
});

interface PropTypes {
  options: Array<{
    name: string;
    callback: () => void;
  }>;
  size?: 'small' | 'medium' | 'large';
  color?: 'primary' | 'secondary';
}

const MultiButton = (props: PropTypes) => {
  const [t] = useTranslation();
  const [open, setOpen] = React.useState(false);
  const classes = useStyles();
  const anchorRef = React.useRef<HTMLDivElement>(null);
  const { options, size, color } = props;

  const handleClick = (selectedOption: number) => {
    options[selectedOption].callback();
  };

  const handleMenuItemClick = (
    event: React.MouseEvent<HTMLLIElement, MouseEvent>,
    index: number,
  ) => {
    setOpen(false);
    handleClick(index);
  };

  const handleToggle = () => {
    setOpen((prevOpen) => !prevOpen);
  };

  const handleClose = (event: React.MouseEvent<Document, MouseEvent>) => {
    if (anchorRef.current && anchorRef.current.contains(event.target as HTMLElement)) {
      return;
    }

    setOpen(false);
  };

  return (
    <div className={classes.root}>
      <Grid container direction="column" alignItems="center">
        <Grid item xs={12}>
          <ButtonGroup
            variant="contained"
            color={color}
            size={size}
            className={classes.button}
            ref={anchorRef}
            aria-label="split button"
          >
            <Button onClick={() => handleClick(0)}>{t(options[0].name)}</Button>
            <Button
              color={color}
              size={size}
              aria-controls={open ? 'split-button-menu' : undefined}
              aria-expanded={open ? 'true' : undefined}
              aria-label="select merge strategy"
              aria-haspopup="menu"
              onClick={handleToggle}
            >
              <ArrowDropDownIcon />
            </Button>
          </ButtonGroup>
          <Popper
            open={open}
            anchorEl={anchorRef.current}
            role={undefined}
            transition
            disablePortal
            style={{
              zIndex: 10,
            }}
          >
            {({ TransitionProps, placement }) => (
              <Grow
                // eslint-disable-next-line react/jsx-props-no-spreading
                {...TransitionProps}
                style={{
                  transformOrigin: placement === 'bottom' ? 'center top' : 'center bottom',
                }}
              >
                <Paper>
                  <ClickAwayListener onClickAway={handleClose}>
                    <MenuList id="split-button-menu">
                      {options.map((option, index) => (
                        <MenuItem
                          key={option.name}
                          onClick={(event) => handleMenuItemClick(event, index)}
                        >
                          {t(option.name)}
                        </MenuItem>
                      ))}
                    </MenuList>
                  </ClickAwayListener>
                </Paper>
              </Grow>
            )}
          </Popper>
        </Grid>
      </Grid>
    </div>
  );
};

MultiButton.defaultProps = {
  size: 'medium',
  color: 'primary',
};

export default MultiButton;
