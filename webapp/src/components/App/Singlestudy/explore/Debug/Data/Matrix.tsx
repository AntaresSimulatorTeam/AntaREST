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

import { MatrixStats } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import type { DataCompProps } from "../utils";

function Matrix({ studyId, filename, filePath, canEdit }: DataCompProps) {
  return (
    <MatrixInput
      title={filename}
      study={studyId}
      url={filePath}
      computStats={MatrixStats.NOCOL}
      disableImport={!canEdit}
    />
  );
}

export default Matrix;
