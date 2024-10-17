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

export const TaskStatus = {
  Pending: 1,
  Running: 2,
  Completed: 3,
  Failed: 4,
  Timeout: 5,
  Cancelled: 6,
} as const;

export const TaskType = {
  Export: "EXPORT",
  VariantGeneration: "VARIANT_GENERATION",
  Copy: "COPY",
  Archive: "ARCHIVE",
  Unarchive: "UNARCHIVE",
  Scan: "SCAN",
  UpgradeStudy: "UPGRADE_STUDY",
  ThermalClusterSeriesGeneration: "THERMAL_CLUSTER_SERIES_GENERATION",
  SnapshotClearing: "SNAPSHOT_CLEARING",
} as const;
