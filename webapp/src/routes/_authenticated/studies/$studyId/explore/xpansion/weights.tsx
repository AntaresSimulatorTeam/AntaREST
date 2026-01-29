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

import { createFileRoute } from "@tanstack/react-router";
import {
  addWeight,
  deleteWeight,
  getAllWeights,
  getWeight,
} from "../../../../../../services/api/xpansion";
import FileList from "./-shared/components/FileList";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/xpansion/weights")({
  component: Weights,
});

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
