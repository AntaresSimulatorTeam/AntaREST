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

import { Box, Typography, Divider } from "@mui/material";
import { formatGridNumber } from "../../shared/utils";

interface MatrixStatsProps {
  stats: {
    count: number;
    sum: number;
    average: number;
    min: number;
    max: number;
  } | null;
}

function MatrixStats({ stats }: MatrixStatsProps) {
  const statItems = [
    { label: "Nb", value: stats?.count ?? 0 },
    { label: "Total", value: formatGridNumber({ value: stats?.sum ?? 0 }) },
    {
      label: "Avg",
      value: formatGridNumber({ value: stats?.average ?? 0, maxDecimals: 2 }),
    },
    { label: "Min", value: formatGridNumber({ value: stats?.min ?? 0 }) },
    { label: "Max", value: formatGridNumber({ value: stats?.max ?? 0 }) },
  ];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        flex: 1,
        alignItems: "center",
        justifyContent: "flex-end",
        width: 1,
        px: 1,
      }}
    >
      {statItems.map((item, index) => (
        <Box
          key={item.label}
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Typography
            sx={{
              display: "flex",
              p: 0.5,
              alignItems: "center",
              color: "lightgray",
              fontSize: 10,
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}
          >
            {item.label}
          </Typography>
          <Typography
            sx={{
              display: "flex",
              alignItems: "center",
              fontSize: 15,
            }}
          >
            {item.value}
          </Typography>
          {index < statItems.length - 1 && (
            <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          )}
        </Box>
      ))}
    </Box>
  );
}

export default MatrixStats;
