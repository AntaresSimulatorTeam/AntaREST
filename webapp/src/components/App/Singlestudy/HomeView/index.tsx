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

import { Box } from "@mui/material";
import { useNavigate } from "react-router-dom";
import Split from "react-split";
import type { StudyMetadata, VariantTree } from "../../../../types/types";
import InformationView from "./InformationView";
import "./Split.css";
import StudyTreeView from "./StudyTreeView";

interface Props {
  study: StudyMetadata;
  variantTree: VariantTree;
}

function HomeView({ study, variantTree }: Props) {
  const navigate = useNavigate();

  return (
    <Split
      className="split"
      gutterSize={4}
      snapOffset={0}
      sizes={[36, 64]}
      style={{
        display: "flex",
        flexDirection: "row",
        flex: 1,
      }}
    >
      {/* Left */}
      <Box
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="flex-start"
        boxSizing="border-box"
        overflow="hidden"
        px={1}
      >
        <StudyTreeView
          study={study}
          variantTree={variantTree}
          onClick={(studyId: string) => navigate(`/studies/${studyId}`)}
        />
      </Box>
      {/* Right */}
      <InformationView study={study} variantTree={variantTree} />
    </Split>
  );
}

export default HomeView;
