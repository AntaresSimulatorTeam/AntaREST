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

import { Backdrop, Box, CircularProgress } from "@mui/material";

interface BackdropLoadingProps {
  open: boolean;
  children?: React.ReactNode;
}

function BackdropLoading(props: BackdropLoadingProps) {
  const { open, children } = props;

  const Comp = (
    <Backdrop
      open={open}
      sx={{
        position: "absolute",
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <CircularProgress color="primary" />
    </Backdrop>
  );

  if (children) {
    return (
      <Box sx={{ position: "relative" }}>
        {children}
        {Comp}
      </Box>
    );
  }

  return Comp;
}

export default BackdropLoading;
