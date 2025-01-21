/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Box } from "@mui/material";
import SplitView, { type SplitViewProps } from "../../../../../../common/SplitView";
import HydroMatrix from "./HydroMatrix";
import type { HydroMatrixType } from "./utils";

interface Props {
  types: [HydroMatrixType, HydroMatrixType];
  direction?: SplitViewProps["direction"];
  sizes: [number, number];
  form?: React.ComponentType;
}

function SplitHydroMatrix({ types, direction, sizes, form: Form }: Props) {
  return (
    <>
      {Form && (
        <Box sx={{ width: 1, p: 1 }}>
          <Form />
        </Box>
      )}
      <SplitView id={`hydro-${types[0]}-${types[1]}`} direction={direction} sizes={sizes}>
        <HydroMatrix type={types[0]} />
        <HydroMatrix type={types[1]} />
      </SplitView>
    </>
  );
}

export default SplitHydroMatrix;
