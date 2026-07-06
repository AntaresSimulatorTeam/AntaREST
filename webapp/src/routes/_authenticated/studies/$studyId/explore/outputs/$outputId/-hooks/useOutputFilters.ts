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

import { useContext } from "react";
import OutputContext from "../-components/OutputMatrixViewer2/OutputContext";

function useOutputFilters() {
  const filters = useContext(OutputContext);

  if (!filters) {
    throw new Error("useOutputFilters() must be used within a <FiltersContext>");
  }

  return filters;
}

export default useOutputFilters;
