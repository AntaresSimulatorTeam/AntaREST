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
  getAllConstraints,
  deleteConstraints,
  getConstraint,
  addConstraints,
} from "../../../../../services/api/xpansion";
import FileList from "./FileList";

function Constraints() {
  return (
    <FileList
      addResource={addConstraints}
      deleteResource={deleteConstraints}
      fetchResourceContent={getConstraint}
      listResources={getAllConstraints}
      errorMessages={{
        add: "xpansion.error.addFile",
        delete: "xpansion.error.deleteFile",
        list: "xpansion.error.loadConfiguration",
        fetchOne: "xpansion.error.getFile",
      }}
      title="global.files"
    />
  );
}

export default Constraints;
