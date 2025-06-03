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

import type { SvgIconComponent } from "@mui/icons-material";
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  styled,
  type DialogContentProps,
  type DialogProps,
} from "@mui/material";
import * as RA from "ramda-adjunct";
import { mergeSxProp } from "../../../utils/muiUtils";

type AlertValue = "success" | "error" | "info" | "warning";

export interface BasicDialogProps extends Omit<DialogProps, "title"> {
  title?: React.ReactNode;
  titleIcon?: SvgIconComponent;
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
  borderColor: theme.palette[$type].main,
}));

function BasicDialog(props: BasicDialogProps) {
  const { title, titleIcon, children, actions, alert, contentProps, ...dialogProps } = props;
  const TitleIcon = titleIcon;

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
        sx={mergeSxProp({ display: "flex", flexDirection: "column" }, contentProps?.sx)}
      >
        {RA.isString(children) ? <DialogContentText>{children}</DialogContentText> : children}
      </DialogContent>
      {actions && <DialogActions>{actions}</DialogActions>}
    </Dialog>
  );
}

export default BasicDialog;
