/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import { getConfig } from "../../services/config";

function Api() {
  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      alignItems="center"
      boxSizing="border-box"
      overflow="auto"
      sx={{ backgroundColor: "#eee" }}
    >
      <Box sx={{ zIndex: 999 }}>
        <SwaggerUI
          url={`${getConfig().baseUrl}${getConfig().restEndpoint}/openapi.json`}
        />
      </Box>
    </Box>
  );
}

export default Api;
