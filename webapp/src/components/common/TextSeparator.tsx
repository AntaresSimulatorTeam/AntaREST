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

import { Box, Divider, SxProps, Theme, Typography } from "@mui/material";

interface Props {
  text: string;
  rootStyle?: SxProps<Theme> | undefined;
  textStyle?: SxProps<Theme> | undefined;
}
function TextSeparator(props: Props) {
  const { text, rootStyle, textStyle } = props;
  return (
    <Box
      width="100%"
      display="flex"
      flexDirection="row"
      justifyContent="flex-start"
      alignItems="center"
      sx={rootStyle}
    >
      <Typography variant="caption" sx={{ ...textStyle }}>
        {text}
      </Typography>
      <Divider
        sx={{
          bgcolor: "rgba(255, 255, 255, 0.09)",
          flexGrow: 1,
          ml: 1,
          height: "2px",
        }}
      />
    </Box>
  );
}

export default TextSeparator;
