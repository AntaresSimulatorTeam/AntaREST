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

import { useNavigate } from "react-router-dom";
import { Box } from "@mui/material";
import Split from "react-split";
import { StudyMetadata, VariantTree } from "@/common/types";
import "./Split.css";
import StudyTreeView from "./StudyTreeView";
import InformationView from "./InformationView";

interface Props {
  study: StudyMetadata | undefined;
  tree: VariantTree | undefined;
}

function HomeView(props: Props) {
  const navigate = useNavigate();
  const { study, tree } = props;

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
      <Box
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="flex-start"
        boxSizing="border-box"
        overflow="hidden"
        px={2}
      >
        <StudyTreeView
          study={study}
          tree={tree}
          onClick={(studyId: string) => navigate(`/studies/${studyId}`)}
        />
      </Box>
      <Box
        height="100%"
        display="flex"
        flexDirection="row"
        justifyContent="flex-start"
        alignItems="flex-start"
        boxSizing="border-box"
        overflow="hidden"
        sx={{ overflowX: "auto" }}
      >
        <Box
          flex={1}
          minWidth="700px"
          height="100%"
          display="flex"
          flexDirection="column"
          justifyContent="center"
          alignItems="center"
          boxSizing="border-box"
          overflow="hidden"
        >
          <InformationView study={study} tree={tree} />
        </Box>
      </Box>
    </Split>
  );
}

export default HomeView;
