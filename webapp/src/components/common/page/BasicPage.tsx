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

import { Box, Divider } from "@mui/material";

interface Props {
  header?: React.ReactNode;
  hideHeaderDivider?: boolean;
}

function BasicPage(props: React.PropsWithChildren<Props>) {
  const { header, hideHeaderDivider, children } = props;

  return (
    <Box sx={{ height: 1, display: "flex", flexDirection: "column" }}>
      {header && (
        <Box sx={{ width: 1, py: 2, px: 3 }}>
          {header}
          {hideHeaderDivider ? null : <Divider />}
        </Box>
      )}
      {children}
    </Box>
  );
}

export default BasicPage;
