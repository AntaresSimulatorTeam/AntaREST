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
import { StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Root } from "./style";
import { MATRICES, HydroMatrixType } from "./utils";

interface Props {
  type: HydroMatrixType;
}

function HydroMatrix({ type }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  const hydroMatrix = MATRICES[type];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title={hydroMatrix.title}
        columnsNames={hydroMatrix.cols}
        rowNames={hydroMatrix.rows}
        study={study}
        url={hydroMatrix.url.replace("{areaId}", areaId)}
        computStats={hydroMatrix.stats}
        fetchFn={hydroMatrix.fetchFn}
        disableEdit={hydroMatrix.disableEdit}
        enablePercentDisplay={hydroMatrix.enablePercentDisplay}
      />
    </Root>
  );
}

export default HydroMatrix;
