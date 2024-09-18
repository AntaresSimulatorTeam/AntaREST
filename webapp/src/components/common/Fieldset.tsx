/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Box, BoxProps, Divider, Typography } from "@mui/material";
import * as RA from "ramda-adjunct";
import { mergeSxProp } from "../../utils/muiUtils";

interface FieldsetProps extends Omit<BoxProps, "component"> {
  legend?: string | React.ReactNode;
  children: React.ReactNode;
  contentProps?: BoxProps;
  fullFieldWidth?: boolean;
  fieldWidth?: number;
}

function Fieldset(props: FieldsetProps) {
  const {
    legend,
    children,
    sx,
    contentProps,
    fullFieldWidth = false,
    fieldWidth = 220,
    ...rest
  } = props;

  return (
    <Box
      {...rest}
      component="fieldset"
      sx={mergeSxProp(
        {
          border: "none",
          m: 0,
          p: 0,
          pb: 5,
          "> .MuiBox-root": {
            display: "flex",
            flexWrap: "wrap",
            gap: 2,
            ".MuiFormControl-root": {
              width: fullFieldWidth ? 1 : fieldWidth,
              m: 0,
            },
          },
          // Remove padding from the last child of the dialog content
          ".MuiDialogContent-root .Form__Content > &:last-child": {
            pb: 0,
          },
        },
        sx,
      )}
    >
      {legend && (
        <>
          {RA.isString(legend) ? (
            <Typography
              variant="h5"
              sx={{ fontSize: "1.25rem", fontWeight: 400, lineHeight: 1.334 }}
            >
              {legend}
            </Typography>
          ) : (
            legend
          )}
          <Divider sx={{ mt: 1 }} />
        </>
      )}
      <Box {...contentProps} sx={mergeSxProp({ pt: 1 }, contentProps?.sx)}>
        {children}
      </Box>
    </Box>
  );
}

Fieldset.Break = function Break() {
  return <Box sx={{ flexBasis: "100%" }} />;
};

export default Fieldset;
