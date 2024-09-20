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
import { MatrixStats, StudyMetadata } from "../../../../../../common/types";
import { Root, Content } from "./style";
import MatrixInput from "../../../../../common/MatrixInput";

interface Props {
  path: string;
}

function Matrix({ path }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <Content>
        <MatrixInput study={study} url={path} computStats={MatrixStats.NOCOL} />
      </Content>
    </Root>
  );
}

export default Matrix;
