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

import GridOffIcon from "@mui/icons-material/GridOff";
import { Skeleton } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import DataGridViewer from "../../../../../../common/DataGridViewer";
import { generateCustomColumns } from "../../../../../../common/Matrix/shared/utils";
import EmptyView from "../../../../../../common/page/EmptyView";
import ViewWrapper from "../../../../../../common/page/ViewWrapper";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

export interface SynthesisData {
  columns: string[];
  data: string[][];
}

interface SynthesisViewerProps {
  synthesisRes: UsePromiseResponse<SynthesisData | null>;
}

function SynthesisViewer({ synthesisRes }: SynthesisViewerProps) {
  const { t } = useTranslation();

  return (
    <ViewWrapper flex>
      <UsePromiseCond
        response={synthesisRes}
        ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
        ifFulfilled={(matrix) => {
          if (!matrix) {
            return <EmptyView title={t("study.results.noData")} icon={GridOffIcon} />;
          }

          return (
            <DataGridViewer
              data={matrix.data}
              columns={generateCustomColumns({
                titles: matrix.columns,
              })}
            />
          );
        }}
      />
    </ViewWrapper>
  );
}

export default SynthesisViewer;
