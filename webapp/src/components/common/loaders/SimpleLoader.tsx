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

import { useTranslation } from "react-i18next";
import { Box, CircularProgress } from "@mui/material";

interface PropTypes {
  progress?: number;
  message?: string;
  color?: string;
}

function SimpleLoader(props: PropTypes) {
  const [t] = useTranslation();
  const { progress, message, color = "rgba(0,0,0,0)" } = props;
  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      position="relative"
      width="100%"
      height="100%"
      zIndex={999}
    >
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        position="absolute"
        width="100%"
        height="100%"
        zIndex={999}
      >
        <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center">
          {progress === undefined ? (
            <CircularProgress sx={{ width: "98px", height: "98px" }} />
          ) : (
            <CircularProgress
              variant="determinate"
              sx={{ width: "98px", height: "98px" }}
              value={progress}
            />
          )}
          {message && <Box mt={2}>{t(message)}</Box>}
        </Box>
      </Box>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        position="absolute"
        width="100%"
        height="100%"
        zIndex={998}
        sx={{ opacity: 0.9, bgcolor: color }}
      />
    </Box>
  );
}

export default SimpleLoader;
