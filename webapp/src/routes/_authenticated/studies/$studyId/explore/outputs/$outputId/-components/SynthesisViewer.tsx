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
import usePromise from "@/hooks/usePromise";
import { getStudyData } from "@/services/api/study";
import GridOffIcon from "@mui/icons-material/GridOff";
import { useTranslation } from "react-i18next";
import useOutput from "../-hooks/useOutput";
import { createOutputDataPath, type GridType } from "../-utils";
import useStudy from "../../../../-hooks/useStudy";

interface SynthesisViewerProps {
  gridType: GridType;
}

interface SynthesisData {
  columns: string[];
  data: string[][];
}

function SynthesisViewer({ gridType }: SynthesisViewerProps) {
  const { t } = useTranslation();
  const study = useStudy();
  const output = useOutput();

  const response = usePromise(
    () => {
      return getStudyData<SynthesisData | null>(
        study.id,
        createOutputDataPath({ output, gridType }),
      );
    },
    {
      deps: [study.id, output, gridType],
    },
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper flex>
      <UsePromiseCond
        response={response}
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
