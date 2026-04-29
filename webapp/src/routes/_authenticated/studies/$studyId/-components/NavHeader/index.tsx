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

import usePromise from "@/hooks/usePromise";
import { studyQueries } from "@/queries/studies/queries";
import { getVariantParents } from "@/services/api/studies/variants";
import { countDescendants, findNodeInTree } from "@/services/utils";
import { WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import { addWsEventListener } from "@/services/webSocket/ws";
import { Stack } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useMatch } from "@tanstack/react-router";
import { useEffect } from "react";
import useStudy from "../../-hooks/useStudy";
import Actions from "./Actions";
import Breadcrumb from "./Breadcrumb";
import Details from "./Details";

function NavHeader() {
  const study = useStudy();
  const match = useMatch({ from: "/_authenticated/studies/$studyId/explore", shouldThrow: false });
  const { data: variantTree } = useSuspenseQuery(studyQueries.variantTree(study.id));
  const isExplorer = !!match;

  const { data: studyMetadata, reload: reloadStudyMetadata } = usePromise(async () => {
    const parents = await getVariantParents({ studyId: study.id });
    const parentStudy = parents.length > 0 ? parents[0] : undefined;

    const tree = findNodeInTree(study.id, variantTree);
    const variantNb = tree ? countDescendants(tree) : 0;

    return { parentStudy, variantNb };
  }, [study]);

  // Reload the promise when the study is edited
  useEffect(() => {
    const listener = (event: WsEvent) => {
      if (event.type === WsEventType.StudyEdited || event.type === WsEventType.StudyDataEdited) {
        if (event.payload.id === study.id) {
          reloadStudyMetadata();
        }
      }
    };

    return addWsEventListener(listener);
  }, [study.id, reloadStudyMetadata]);

  const { parentStudy, variantNb } = studyMetadata || {};

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Stack
      spacing={1}
      sx={[
        { px: 1 },
        !isExplorer && { borderBottom: (theme) => `1px solid ${theme.vars.palette.divider}` },
      ]}
    >
      <Breadcrumb />
      <Details parentStudy={parentStudy} variantNb={variantNb} />
      <Actions parentStudy={parentStudy} variantNb={variantNb} isExplorer={isExplorer} />
    </Stack>
  );
}

export default NavHeader;
