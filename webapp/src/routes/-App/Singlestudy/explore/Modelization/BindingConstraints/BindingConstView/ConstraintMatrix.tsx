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

import Matrix from "@/components/Matrix";
import SplitView from "@/components/page/SplitView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import { getBindingConstraint } from "@/services/api/studydata";
import { Box, Skeleton } from "@mui/material";
import { useTranslation } from "react-i18next";
import semver from "semver";
import type { StudyMetadata } from "../../../../../../../types/types";

interface Props {
  study: StudyMetadata;
  constraintId: string;
}

const URL_BASE = "input/bindingconstraints/" as const;

function ConstraintMatrix({ study, constraintId }: Props) {
  const { t } = useTranslation();

  const constraintRes = usePromise(
    () => getBindingConstraint(study.id, constraintId),
    [study.id, constraintId],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (semver.lt(study.version, "8.7.0")) {
    return (
      <Matrix
        studyId={study.id}
        title={t("global.matrix")}
        url={`${URL_BASE}${constraintId}`}
        customColumns={["<", ">", "="]}
      />
    );
  }

  return (
    <UsePromiseCond
      response={constraintRes}
      ifFulfilled={({ operator }) => (
        <Box sx={{ height: 1, width: 1 }}>
          {operator === "less" && (
            <Matrix
              studyId={study.id}
              title={t("study.modeling.bindingConst.timeSeries.less")}
              url={`${URL_BASE}${constraintId}_lt`}
            />
          )}
          {operator === "equal" && (
            <Matrix
              studyId={study.id}
              title={t("study.modeling.bindingConst.timeSeries.equal")}
              url={`${URL_BASE}${constraintId}_eq`}
            />
          )}
          {operator === "greater" && (
            <Matrix
              studyId={study.id}
              title={t("study.modeling.bindingConst.timeSeries.greater")}
              url={`${URL_BASE}${constraintId}_gt`}
            />
          )}
          {operator === "both" && (
            <SplitView splitId="binding-constraints-matrix" sizes={[50, 50]}>
              <Box sx={{ px: 2 }}>
                <Matrix
                  studyId={study.id}
                  title={t("study.modeling.bindingConst.timeSeries.less")}
                  url={`${URL_BASE}${constraintId}_lt`}
                />
              </Box>
              <Box sx={{ px: 2 }}>
                <Matrix
                  studyId={study.id}
                  title={t("study.modeling.bindingConst.timeSeries.greater")}
                  url={`${URL_BASE}${constraintId}_gt`}
                />
              </Box>
            </SplitView>
          )}
        </Box>
      )}
      ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
    />
  );
}

export default ConstraintMatrix;
