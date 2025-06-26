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

import { Box } from "@mui/material";
import type { StudyMetadata } from "../../../../types/types";
import Actions from "./Actions";
import Details from "./Details";

interface Props {
  study: StudyMetadata;
  parentStudy?: StudyMetadata;
  variantNb: number;
  isExplorer?: boolean;
}

function NavHeader({ study, parentStudy, variantNb, isExplorer }: Props) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: 1,
        py: 1,
        px: 2,
        overflow: "hidden",
        gap: 1,
      }}
    >
      <Actions
        study={study}
        parentStudy={parentStudy}
        variantNb={variantNb}
        isExplorer={isExplorer}
      />
      <Details study={study} parentStudy={parentStudy} variantNb={variantNb} />
    </Box>
  );
}

export default NavHeader;
