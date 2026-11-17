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

import { Stack } from "@mui/material";
import { useMatch } from "@tanstack/react-router";
import Actions from "./Actions";
import Breadcrumb from "./Breadcrumb";
import Details from "./Details";

function NavHeader() {
  const isExplorerRoute = !!useMatch({
    from: "/_authenticated/studies/$studyId/explore",
    shouldThrow: false,
  });

  return (
    <Stack
      spacing={1}
      sx={[
        { px: 1 },
        !isExplorerRoute && { borderBottom: (theme) => `1px solid ${theme.vars.palette.divider}` },
      ]}
    >
      <Breadcrumb />
      <Details />
      <Actions />
    </Stack>
  );
}

export default NavHeader;
