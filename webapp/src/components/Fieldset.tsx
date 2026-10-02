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

import { mergeSxProp } from "@/utils/muiUtils";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Box,
  Collapse,
  Divider,
  IconButton,
  Stack,
  Tooltip,
  type BoxProps,
  type SxProps,
  type Theme,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

interface FieldsetProps {
  legend?: React.ReactNode;
  children: React.ReactNode;
  contentProps?: BoxProps;
  fullFieldWidth?: boolean;
  fieldWidth?: number;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  sx?: SxProps<Theme>;
}

function Fieldset({
  legend,
  children,
  sx,
  contentProps,
  fullFieldWidth = false,
  fieldWidth = 200,
  collapsible = false,
  defaultCollapsed = false,
}: FieldsetProps) {
  const { t } = useTranslation();
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const canCollapse = collapsible && !!legend;
  const isLegendString = typeof legend === "string";

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleToggleCollapse = () => {
    setIsCollapsed((prev) => !prev);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      component="fieldset"
      sx={mergeSxProp(
        {
          border: "none",
          m: 0,
          p: 0,
          pb: 3,
          // Increase padding from the last Fieldset child inside a Form
          ".Form__Content > &:last-child": {
            pb: 2,
          },
          // Remove padding from the last Fieldset child inside a Form that is inside a dialog content
          ".MuiDialogContent-root .Form__Content > &:last-child": {
            pb: 0,
          },
        },
        sx,
      )}
    >
      {legend && (
        <>
          <Stack
            component="legend"
            spacing={0.5}
            {...(canCollapse &&
              isLegendString && { onClick: handleToggleCollapse, sx: { cursor: "pointer" } })}
          >
            {canCollapse && (
              <Tooltip
                title={isCollapsed ? t("button.expand") : t("button.collapse")}
                placement="top"
              >
                <IconButton
                  size="small"
                  onClick={!isLegendString ? handleToggleCollapse : undefined}
                >
                  <ExpandMoreIcon
                    sx={{
                      transform: isCollapsed ? "rotate(0deg)" : "rotate(180deg)",
                      transition: (theme) =>
                        theme.transitions.create("transform", {
                          duration: theme.transitions.duration.shortest,
                        }),
                    }}
                  />
                </IconButton>
              </Tooltip>
            )}
            <Box>{legend}</Box>
          </Stack>
          <Divider sx={{ mt: 1 }} />
        </>
      )}
      <Collapse in={canCollapse ? !isCollapsed : true} timeout="auto">
        <Box
          {...contentProps}
          sx={mergeSxProp(
            {
              pt: legend ? 3 : 1,
              display: "flex",
              flexWrap: "wrap",
              gap: 2,
              // Ignore RadioGroupFE and its children, and FieldSkeleton
              ".MuiFormControl-root:not(:has(> .MuiRadioGroup-root)):not(.MuiRadioGroup-root *), .FieldSkeleton":
                {
                  // If the field hasn't `fullWidth` prop activated
                  "&:not(.MuiFormControl-fullWidth)": {
                    width: fullFieldWidth ? 1 : fieldWidth,
                  },
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
            contentProps?.sx,
          )}
        >
          {children}
        </Box>
      </Collapse>
    </Box>
  );
}

Fieldset.Break = function Break() {
  return <Box sx={{ flexBasis: "100%" }} />;
};

export default Fieldset;
