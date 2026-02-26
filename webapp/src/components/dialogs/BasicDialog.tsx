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

import type { SvgIconComponent } from "@mui/icons-material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import InfoIcon from "@mui/icons-material/Info";
import WarningIcon from "@mui/icons-material/Warning";
import {
  Dialog,
  DialogActions,
  DialogContent,
  type DialogContentProps,
  DialogContentText,
  type DialogProps,
  DialogTitle,
  styled,
} from "@mui/material";
import * as RA from "ramda-adjunct";
import { mergeSxProp } from "@/utils/muiUtils";

type AlertValue = "success" | "error" | "info" | "warning";

export interface BasicDialogProps extends Omit<DialogProps, "title"> {
  title?: React.ReactNode;
  titleIcon?: SvgIconComponent; // TODO: convert to React.ReactNode for consistency
  actions?: React.ReactNode;
  alert?: AlertValue;
  contentProps?: DialogContentProps;
}

const AlertBorder = styled("span", {
  shouldForwardProp: (prop: string) => !prop.startsWith("$"),
})<{ $type: AlertValue }>(({ theme, $type }) => ({
  position: "absolute",
  top: 0,
  width: "100%",
  borderTop: "4px solid",
  borderColor: theme.vars.palette[$type].main,
}));

const titleIconByAlert: Record<AlertValue, SvgIconComponent> = {
  success: CheckCircleIcon,
  error: ErrorIcon,
  info: InfoIcon,
  warning: WarningIcon,
};

function BasicDialog({
  title,
  titleIcon,
  children,
  actions,
  alert,
  contentProps,
  fullScreen = false,
  sx,
  ...dialogProps
}: BasicDialogProps) {
  const TitleIcon = titleIcon || (alert ? titleIconByAlert[alert] : null);

  return (
    <Dialog
      {...dialogProps}
      fullScreen={fullScreen}
      sx={mergeSxProp(
        [
          fullScreen && {
            top: 20,
            bottom: 20,
            left: 20,
            right: 20,
            ".MuiDialog-paperFullScreen": {
              borderRadius: 1,
            },
          },
        ],
        sx,
      )}
    >
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
        sx={mergeSxProp({ display: "flex", flexDirection: "column" }, contentProps?.sx)}
      >
        {RA.isString(children) ? <DialogContentText>{children}</DialogContentText> : children}
      </DialogContent>
      {actions && <DialogActions>{actions}</DialogActions>}
    </Dialog>
  );
}

export default BasicDialog;
