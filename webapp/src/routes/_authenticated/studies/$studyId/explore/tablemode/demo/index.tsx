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

import DataGridForm from "@/components/DataGridForm";
import ViewWrapper from "@/components/page/ViewWrapper";
import type { GridColumn } from "@glideapps/glide-data-grid";
import { Box, Typography } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";

////////////////////////////////////////////////////////////////
// Fake data — mimics a "thermals" table-mode view where rows are
// thermal clusters and group-header rows represent their group names.
////////////////////////////////////////////////////////////////

type RowData = Record<string, string | boolean | number>;

/**
 * Each group name key maps to an empty record — those rows are rendered
 * as read-only group-header separators by DataGridForm / DataGrid.
 * Regular cluster rows carry their actual property values.
 */
const FAKE_DATA: Record<string, RowData> = {
  // ── Hard Coal ──────────────────────────────────────────────
  "Hard Coal": {},
  hard_coal_baseload: {
    enabled: true,
    unitCount: 2,
    nominalCapacity: 600,
    marginalCost: 45.0,
    minStablePower: 180,
    mustRun: false,
  },
  hard_coal_peaker: {
    enabled: true,
    unitCount: 1,
    nominalCapacity: 300,
    marginalCost: 50.5,
    minStablePower: 90,
    mustRun: false,
  },

  // ── Gas ────────────────────────────────────────────────────
  Gas: {},
  gas_ccgt_nord: {
    enabled: true,
    unitCount: 3,
    nominalCapacity: 450,
    marginalCost: 62.0,
    minStablePower: 135,
    mustRun: false,
  },
  gas_gt_peak: {
    enabled: false,
    unitCount: 2,
    nominalCapacity: 200,
    marginalCost: 85.0,
    minStablePower: 40,
    mustRun: false,
  },
  gas_ccgt_sud: {
    enabled: true,
    unitCount: 2,
    nominalCapacity: 420,
    marginalCost: 60.0,
    minStablePower: 126,
    mustRun: false,
  },

  // ── Nuclear ────────────────────────────────────────────────
  Nuclear: {},
  nuclear_unit_a: {
    enabled: true,
    unitCount: 1,
    nominalCapacity: 1200,
    marginalCost: 8.0,
    minStablePower: 600,
    mustRun: true,
  },
  nuclear_unit_b: {
    enabled: true,
    unitCount: 1,
    nominalCapacity: 1200,
    marginalCost: 8.5,
    minStablePower: 600,
    mustRun: true,
  },
  nuclear_unit_c: {
    enabled: false,
    unitCount: 1,
    nominalCapacity: 900,
    marginalCost: 9.0,
    minStablePower: 450,
    mustRun: false,
  },

  // ── Renewables ─────────────────────────────────────────────
  Renewables: {},
  wind_onshore_1: {
    enabled: true,
    unitCount: 10,
    nominalCapacity: 100,
    marginalCost: 0.0,
    minStablePower: 0,
    mustRun: false,
  },
  solar_farm_a: {
    enabled: true,
    unitCount: 5,
    nominalCapacity: 200,
    marginalCost: 0.0,
    minStablePower: 0,
    mustRun: false,
  },
};

/**
 * The set of row-names that act as group headers.
 * DataGridForm will render these rows with:
 *  - First column (row marker): group name in bold, with header background
 *  - All data columns: empty, read-only, with header background
 */
const GROUP_ROWS = new Set<string>(["Hard Coal", "Gas", "Nuclear", "Renewables"]);

const COLUMNS: Array<GridColumn & { id: string }> = [
  { id: "enabled", title: "Enabled" },
  { id: "unitCount", title: "Unit Count" },
  { id: "nominalCapacity", title: "Nominal Capacity (MW)" },
  { id: "marginalCost", title: "Marginal Cost (€/MWh)" },
  { id: "minStablePower", title: "Min Stable Power (MW)" },
  { id: "mustRun", title: "Must Run" },
];

////////////////////////////////////////////////////////////////
// Route
////////////////////////////////////////////////////////////////

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/tablemode/demo/")({
  component: TableModeGroupRowsDemo,
});

////////////////////////////////////////////////////////////////
// Component
////////////////////////////////////////////////////////////////

function TableModeGroupRowsDemo() {
  return (
    <ViewWrapper>
      {/* Header banner */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
        <Typography variant="h6" noWrap>
          Group Rows Demo — Thermal Clusters
        </Typography>
      </Box>

      {/* DataGridForm with groupRows prop */}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <DataGridForm
          defaultData={FAKE_DATA}
          columns={COLUMNS}
          groupRows={GROUP_ROWS}
          onSubmit={({ dirtyValues }) => {
            // In a real scenario this would call the API.
            // eslint-disable-next-line no-console
            console.info("[GroupRowsDemo] dirty values:", dirtyValues);
            return Promise.resolve();
          }}
          submitButtonText="Save (demo)"
        />
      </Box>
    </ViewWrapper>
  );
}
