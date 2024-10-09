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

import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import { MatrixStats, StudyMetadata } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import { Root } from "./style";

function Reserve() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/reserves/${currentArea}`;
  const colmunsNames = [
    "Primary Res. (draft)",
    "Strategic Res. (draft)",
    "DSM",
    "Day Ahead",
  ];

  return (
    <Root>
      <MatrixInput
        study={study}
        url={url}
        columnsNames={colmunsNames}
        computStats={MatrixStats.TOTAL}
      />
    </Root>
  );
}

export default Reserve;
