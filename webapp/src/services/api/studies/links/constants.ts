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

export const TransmissionCapacity = {
  Infinite: "infinite",
  Ignore: "ignore",
  Enabled: "enabled",
} as const;

export const AssetType = {
  AC: "ac",
  DC: "dc",
  Gaz: "gaz",
  Virt: "virt",
  Other: "other",
} as const;

export const LinkStyle = {
  Dot: "dot",
  Plain: "plain",
  Dash: "dash",
  DotDash: "dotdash",
  Other: "other",
} as const;
