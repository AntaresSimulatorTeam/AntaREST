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
  getAllCapacities,
  deleteCapacity,
  getCapacity,
  addCapacity,
} from "@/services/api/xpansion";
import FileList from "./FileList";

function Capacities() {
  return (
    <FileList
      addResource={addCapacity}
      deleteResource={deleteCapacity}
      fetchResourceContent={getCapacity}
      listResources={getAllCapacities}
      errorMessages={{
        add: "xpansion.error.addFile",
        delete: "xpansion.error.deleteFile",
        list: "xpansion.error.loadConfiguration",
        fetchOne: "xpansion.error.getFile",
      }}
      title="xpansion.capacities"
      isMatrix
    />
  );
}

export default Capacities;
