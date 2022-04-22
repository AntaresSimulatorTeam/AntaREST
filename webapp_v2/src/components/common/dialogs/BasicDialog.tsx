import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogProps,
  DialogTitle,
  IconButton,
  styled,
  experimental_sx as sx,
} from "@mui/material";
import { ElementType, ReactNode } from "react";
import * as RA from "ramda-adjunct";
import { SvgIconComponent } from "@mui/icons-material";
import CloseIcon from "@mui/icons-material/Close";
import * as R from "ramda";

/**
 * Types
 */

enum Alert {
  "success",
  "error",
  "warning",
  "info",
}

export interface BasicDialogProps extends DialogProps {
  open: boolean;
  title?: string;
  titleIcon?: ElementType<SvgIconComponent>;
  actions?: ReactNode;
  alert?: keyof typeof Alert;
  noCloseIcon?: boolean;
}

/**
 * Styled
 */

const AlertBorder = styled("span", {
  shouldForwardProp: (prop: string) => !prop.startsWith("$"),
})<{ $type: keyof typeof Alert }>(({ $type }) =>
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
  const {
    title,
    titleIcon,
    children,
    actions,
    alert,
    noCloseIcon,
    ...dialogProps
  } = props;
  const { onClose } = dialogProps;
  const TitleIcon = titleIcon as SvgIconComponent;

  return (
    <Dialog {...dialogProps}>
      {alert && <AlertBorder $type={alert} />}
      {(title || TitleIcon || onClose) && (
        <DialogTitle sx={{ mr: onClose ? 4 : 0 }}>
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
          {onClose && !noCloseIcon && (
            <IconButton
              onClick={onClose as () => void}
              sx={{
                position: "absolute",
                right: 8,
                top: 8,
                color: (theme) => theme.palette.grey[500],
              }}
            >
              <CloseIcon />
            </IconButton>
          )}
        </DialogTitle>
      )}
      {RA.isString(children) ? (
        <DialogContent>
          <DialogContentText>{children}</DialogContentText>
        </DialogContent>
      ) : (
        children
      )}
      {actions && <DialogActions>{actions}</DialogActions>}
    </Dialog>
  );
}

BasicDialog.defaultProps = {
  title: null,
  titleIcon: null,
  actions: null,
  alert: false,
  noCloseIcon: false,
};

export default BasicDialog;
