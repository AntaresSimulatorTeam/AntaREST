/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import Matrix from "../../../../../common/Matrix";

function MiscGen() {
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/misc-gen/miscgen-${currentArea}`;
  const columns = [
    "CHP",
    "Bio Mass",
    "Bio Gaz",
    "Waste",
    "GeoThermal",
    "Other",
    "PSP",
    "ROW Balance",
  ];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Matrix url={url} customColumns={columns} aggregateColumns={["total"]} isTimeSeries={false} />
  );
}

export default MiscGen;
