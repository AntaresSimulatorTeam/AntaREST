import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogProps,
  DialogTitle,
  styled,
  DialogContentProps,
} from "@mui/material";
import * as RA from "ramda-adjunct";
import { SvgIconComponent } from "@mui/icons-material";
import * as R from "ramda";
import { mergeSxProp } from "../../../utils/muiUtils";

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

export interface BasicDialogProps extends Omit<DialogProps, "title"> {
  title?: React.ReactNode;
  titleIcon?: SvgIconComponent;
  actions?: React.ReactNode;
  alert?: AlertValues;
  contentProps?: DialogContentProps;
}

/**
 * Styled
 */

const AlertBorder = styled("span", {
  shouldForwardProp: (prop: string) => !prop.startsWith("$"),
})<{ $type: AlertValues }>(({ theme, $type }) => ({
  position: "absolute",
  top: 0,
  width: "100%",
  borderTop: "4px solid",
  borderColor: R.cond([
    [R.equals(Alert.success), () => theme.palette.success.main],
    [R.equals(Alert.error), () => theme.palette.error.main],
    [R.equals(Alert.warning), () => theme.palette.warning.main],
    [R.equals(Alert.info), () => theme.palette.info.main],
  ])(Alert[$type]),
}));

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
    contentProps,
    ...dialogProps
  } = props;
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
      <DialogContent
        {...contentProps}
        sx={mergeSxProp(
          { display: "flex", flexDirection: "column" },
          contentProps?.sx
        )}
      >
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
  contentProps: null,
};

export default BasicDialog;
