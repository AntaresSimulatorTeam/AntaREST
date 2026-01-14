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

import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudies } from "@/redux/selectors";
import { Box } from "@mui/material";
import ExternalTree from "./ExternalTree";

function StudyTree() {
  const studies = useAppSelector(getStudies);
  const dispatch = useAppDispatch();

  // Filter studies by management type
  const externalStudies = studies.filter((s) => !s.managed);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleNodeClick = (itemId: string) => {
    dispatch(updateStudyFilters({ folder: itemId }));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ p: 2, pt: 0 }}>
      <ExternalTree studies={externalStudies} onNodeClick={handleNodeClick} />
    </Box>
  );
}

export default StudyTree;
