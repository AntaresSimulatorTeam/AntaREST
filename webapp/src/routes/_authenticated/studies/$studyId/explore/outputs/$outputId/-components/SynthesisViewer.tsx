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

import DataGridSkeleton from "@/components/DataGridSkeleton";
import DataGridViewer from "@/components/DataGridViewer";
import { generateCustomColumns } from "@/components/Matrix/shared/utils";
import EmptyView from "@/components/page/EmptyView";
import ViewWrapper from "@/components/page/ViewWrapper";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import GridOffIcon from "@mui/icons-material/GridOff";
import { useTranslation } from "react-i18next";

export interface SynthesisData {
  columns: string[];
  data: string[][];
}

interface SynthesisViewerProps {
  synthesisRes: UsePromiseResponse<SynthesisData | null>;
}

function SynthesisViewer({ synthesisRes }: SynthesisViewerProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper flex>
      <UsePromiseCond
        response={synthesisRes}
        ifPending={() => <DataGridSkeleton />}
        ifFulfilled={(matrix) => {
          if (!matrix) {
            return <EmptyView title={t("study.outputs.noData")} icon={GridOffIcon} />;
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
