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

import Matrix from "../../../../../common/Matrix";
import type { DataCompProps } from "../utils";

function DebugMatrix({ studyId, filename, filePath, canEdit }: DataCompProps) {
  return <Matrix title={filename} url={filePath} canImport={!canEdit} />;
}

export default DebugMatrix;
