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

import { mergeSxProp } from "@/utils/muiUtils";
import { Box, type SxProps, type Theme } from "@mui/material";
import SplitView, { type SplitViewProps } from "../../../../../../common/SplitView";
import HydroMatrix from "./HydroMatrix";
import type { HydroMatrixType } from "./utils";

interface Props {
  types: [HydroMatrixType, HydroMatrixType];
  direction?: SplitViewProps["direction"];
  sizes: [number, number];
  form?: React.ComponentType;
  sx?: SxProps<Theme>;
}

function SplitHydroMatrix({ types, direction, sizes, form: Form, sx }: Props) {
  return (
    <Box sx={mergeSxProp({ width: 1, height: 1 }, sx)}>
      {Form && <Form />}
      <SplitView id={`hydro-${types[0]}-${types[1]}`} direction={direction} sizes={sizes}>
        <HydroMatrix type={types[0]} />
        <HydroMatrix type={types[1]} />
      </SplitView>
    </Box>
  );
}

export default SplitHydroMatrix;
