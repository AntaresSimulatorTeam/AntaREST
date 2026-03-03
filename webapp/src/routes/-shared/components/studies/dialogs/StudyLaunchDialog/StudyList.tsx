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

import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudy } from "@/redux/selectors";
import type { StudyMetadata } from "@/types/types";
import { buildKey } from "@/utils/reactUtils";
import { Box, Chip } from "@mui/material";
import { shallowEqual } from "react-redux";

interface Props {
  studyIds: Array<StudyMetadata["id"]>;
}

function StudyList({ studyIds }: Props) {
  const studyNames = useAppSelector(
    (state) => studyIds.map((id) => getStudy(state, id)?.name || id),
    shallowEqual,
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ mx: 1, mb: 2, maxHeight: 95, overflowY: "auto", overflowX: "hidden" }}>
      {studyNames.map((name, index) => (
        <Chip key={buildKey(name, index)} label={name} sx={{ mr: 1, mb: 1 }} />
      ))}
    </Box>
  );
}

export default StudyList;
