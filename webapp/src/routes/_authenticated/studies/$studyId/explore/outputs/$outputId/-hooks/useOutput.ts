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

import { outputQueries } from "@/queries/outputs/queries";
import type { Output } from "@/services/api/studies/outputs/types";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

function useOutput() {
  const { studyId, outputId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/outputs/$outputId/",
  });
  const { t } = useTranslation();

  const getOutput = useCallback(
    (outputs: Output[]) => {
      return outputs.find(({ id }) => id === outputId);
    },
    [outputId],
  );

  const { data: output } = useSuspenseQuery({
    ...outputQueries.list(studyId),
    select: getOutput,
  });

  if (!outputId) {
    throw new Error(t("route.noParameter", { param: "outputId" }));
  }

  if (!output) {
    throw new Error(t("study.outputs.notFound", { id: outputId }));
  }

  return output;
}

export default useOutput;
