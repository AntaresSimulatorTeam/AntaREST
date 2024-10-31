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

import {
  addWeight,
  deleteWeight,
  getWeight,
  getAllWeights,
} from "@/services/api/xpansion";
import FileList from "./FileList";

function Weights() {
  return (
    <FileList
      addResource={addWeight}
      deleteResource={deleteWeight}
      fetchResourceContent={getWeight}
      listResources={getAllWeights}
      errorMessages={{
        add: "xpansion.error.addFile",
        delete: "xpansion.error.deleteFile",
        list: "xpansion.error.loadConfiguration",
        fetchOne: "xpansion.error.getFile",
      }}
      title="xpansion.weights"
      isMatrix
    />
  );
}

export default Weights;
