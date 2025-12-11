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

import Matrix from "@/components/Matrix";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";

function Load() {
  const currentArea = useAppSelector(getCurrentAreaId);
  const study = useStudy();
  const url = `input/load/series/load_${currentArea}`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <Matrix studyId={study.id} url={url} aggregateColumns="stats" />;
}

export default Load;
