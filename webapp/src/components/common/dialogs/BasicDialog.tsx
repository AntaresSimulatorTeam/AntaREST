import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogProps,
  DialogTitle,
  styled,
  experimental_sx as sx,
} from "@mui/material";
import { ElementType, ReactNode } from "react";
import * as RA from "ramda-adjunct";
import { SvgIconComponent } from "@mui/icons-material";
import * as R from "ramda";
import { scrollbarStyle } from "../../../theme";

/**
 * Types
 */

enum Alert {
  success,
  error,
  warning,
  info,
}

type AlertValues = keyof typeof Alert;

export interface BasicDialogProps extends DialogProps {
  title?: string;
  titleIcon?: ElementType<SvgIconComponent>;
  actions?: ReactNode;
  alert?: AlertValues;
}

/**
 * Styled
 */

const AlertBorder = styled("span", {
  shouldForwardProp: (prop: string) => !prop.startsWith("$"),
})<{ $type: AlertValues }>(({ $type }) =>
  sx({
    position: "absolute",
    top: 0,
    width: 1,
    borderTop: 4,
    borderColor: R.cond([
      [R.equals(Alert.success), () => "success.main"],
      [R.equals(Alert.error), () => "error.main"],
      [R.equals(Alert.warning), () => "warning.main"],
      [R.equals(Alert.info), () => "info.main"],
    ])(Alert[$type]),
  })
);

/**
 * Component
 */

function BasicDialog(props: BasicDialogProps) {
  const { title, titleIcon, children, actions, alert, ...dialogProps } = props;
  const TitleIcon = titleIcon as SvgIconComponent;

  return (
    <Dialog {...dialogProps}>
      {alert && <AlertBorder $type={alert} />}
      {(title || TitleIcon) && (
        <DialogTitle>
          {TitleIcon && (
            <TitleIcon
              fontSize="large"
              sx={{
                verticalAlign: "bottom",
                mr: 2,
              }}
            />
          )}
          {title}
        </DialogTitle>
      )}
      <DialogContent sx={{ ...scrollbarStyle }}>
        {RA.isString(children) ? (
          <DialogContentText>{children}</DialogContentText>
        ) : (
          children
        )}
      </DialogContent>
      {actions && <DialogActions>{actions}</DialogActions>}
    </Dialog>
  );
}

BasicDialog.defaultProps = {
  title: null,
  titleIcon: null,
  actions: null,
  alert: false,
};

export default BasicDialog;
