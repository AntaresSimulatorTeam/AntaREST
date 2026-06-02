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

import type { ViewMode } from "../types";
import type { Study } from "@/services/api/studies/types";

export interface BreadcrumbItem {
  label: string;
  id: string | null;
  path: string | null;
}

export interface HeaderProps {
  studyIds: Array<Study["id"]>;
  selectedStudyIds: Array<Study["id"]>;
  setSelectedStudyIds: (ids: Array<Study["id"]>) => void;
  setStudiesToLaunch: (ids: Array<Study["id"]>) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}
