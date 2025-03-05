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

import { Box, Divider, type BoxProps, type SxProps, type Theme } from "@mui/material";
import * as RA from "ramda-adjunct";
import { mergeSxProp } from "@/utils/muiUtils";

interface FieldsetProps {
  legend?: string | React.ReactNode;
  children: React.ReactNode;
  contentProps?: BoxProps;
  fullFieldWidth?: boolean;
  fieldWidth?: number;
  sx?: SxProps<Theme>;
}

function Fieldset(props: FieldsetProps) {
  const { legend, children, sx, contentProps, fullFieldWidth = false, fieldWidth = 200 } = props;

  return (
    <Box
      component="fieldset"
      sx={mergeSxProp(
        {
          border: "none",
          m: 0,
          p: 0,
          pb: 4,
          "> .MuiBox-root": {
            display: "flex",
            flexWrap: "wrap",
            gap: 2,
            ".MuiFormControl-root": {
              width: fullFieldWidth ? 1 : fieldWidth,
              m: 0,
              // SwitchFE
              ".MuiFormControlLabel-root": {
                pl: 1.5,
              },
            },
            ".MuiAutocomplete-root": {
              width: fullFieldWidth ? 1 : fieldWidth,
            },
          },
          // Increase padding from the last child
          ".Form__Content > &:last-child": {
            pb: 2,
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
          {RA.isString(legend) ? <Box component="legend">{legend}</Box> : legend}
          <Divider sx={{ mt: 1 }} />
        </>
      )}
      <Box {...contentProps} sx={mergeSxProp({ pt: legend ? 3 : 1 }, contentProps?.sx)}>
        {children}
      </Box>
    </Box>
  );
}

Fieldset.Break = function Break() {
  return <Box sx={{ flexBasis: "100%" }} />;
};

export default Fieldset;
