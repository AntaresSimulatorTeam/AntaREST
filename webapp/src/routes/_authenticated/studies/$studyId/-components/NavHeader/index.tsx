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

import { variantQueries } from "@/queries/variants/queries";
import type { VariantTree } from "@/services/api/studies/variants/types";
import { countDescendants, getParentNode } from "@/services/utils";
import { Stack } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useMatch } from "@tanstack/react-router";
import { useCallback } from "react";
import useStudy from "../../-hooks/useStudy";
import Actions from "./Actions";
import Breadcrumb from "./Breadcrumb";
import Details from "./Details";

function NavHeader() {
  const study = useStudy();
  const match = useMatch({ from: "/_authenticated/studies/$studyId/explore", shouldThrow: false });
  const isExplorer = !!match;

  const selectStudyDetails = useCallback(
    (tree: VariantTree) => ({
      parentStudy: getParentNode(tree, study.id),
      variantNb: countDescendants(tree, study.id),
    }),
    [study.id],
  );

  const { data: studyDetails } = useSuspenseQuery({
    ...variantQueries.variantTree(study.id),
    select: selectStudyDetails,
  });

  return (
    <Stack
      spacing={1}
      sx={[
        { px: 1 },
        !isExplorer && { borderBottom: (theme) => `1px solid ${theme.vars.palette.divider}` },
      ]}
    >
      <Breadcrumb />
      <Details {...studyDetails} />
      <Actions {...studyDetails} isExplorer={isExplorer} />
    </Stack>
  );
}

export default NavHeader;
