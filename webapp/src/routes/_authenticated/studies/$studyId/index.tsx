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

import SplitView from "@/components/SplitView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import { getVariantParents, getVariantTree } from "@/services/api/variant";
import { Box } from "@mui/material";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import InformationView from "./-components/InformationView";
import StudyTreeView from "./-components/StudyTreeView";
import useStudy from "./-hooks/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/")({
  component: StudyHome,
});

function StudyHome() {
  const study = useStudy();
  const navigate = useNavigate();

  const variantTreeRes = usePromise(async () => {
    const parents = await getVariantParents(study.id);
    const root = parents.length > 0 ? parents[parents.length - 1] : study;
    const variantTree = await getVariantTree(root.id);

    return variantTree;
  }, [study]);

  return (
    <UsePromiseCond
      response={variantTreeRes}
      ifFulfilled={(variantTree) => (
        <SplitView splitId="study-home" gutterSize={4} sizes={[30, 70]}>
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
              onClick={(studyId: string) => navigate({ to: `/studies/${studyId}` })}
            />
          </Box>
          {/* Right */}
          <InformationView study={study} variantTree={variantTree} />
        </SplitView>
      )}
    />
  );
}
