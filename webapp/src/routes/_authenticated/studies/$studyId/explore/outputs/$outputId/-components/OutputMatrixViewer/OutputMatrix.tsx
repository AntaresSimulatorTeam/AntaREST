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
import FilterableMatrixGrid, {
  type FilterableMatrixGridHandle,
} from "@/components/Matrix/components/FilterableMatrixGrid";
import {
  isNonEmptyMatrix,
  type DateTimes,
  type EnhancedGridColumn,
  type ResultMatrixDTO,
} from "@/components/Matrix/shared/types";
import EmptyView from "@/components/page/EmptyView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import type { MatrixIndex } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import GridOffIcon from "@mui/icons-material/GridOff";
import { useTranslation } from "react-i18next";

interface ResultMatrixProps {
  matrixRes: UsePromiseResponse<ResultMatrixDTO | undefined>;
  resultColHeaders: string[][];
  filteredData: number[][];
  resultColumns: EnhancedGridColumn[];
  matrixGridRef: React.RefObject<FilterableMatrixGridHandle>;
  dateTime: DateTimes | undefined;
  dateTimeMetadata: MatrixIndex | undefined;
}

function OutputMatrix({
  matrixRes,
  resultColHeaders,
  filteredData,
  resultColumns,
  matrixGridRef,
  dateTime,
  dateTimeMetadata,
}: ResultMatrixProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={matrixRes}
      ifPending={() => <DataGridSkeleton />}
      ifFulfilled={() => {
        if (resultColHeaders.length === 0) {
          return <DataGridSkeleton />;
        }

        if (!isNonEmptyMatrix(filteredData)) {
          return <EmptyView title={t("study.outputs.noData")} icon={GridOffIcon} />;
        }

        return (
          <FilterableMatrixGrid
            ref={matrixGridRef}
            key={`grid-${resultColHeaders.length}`}
            data={filteredData}
            rows={filteredData.length}
            columns={resultColumns}
            dateTime={dateTime}
            timeFrequency={dateTimeMetadata?.level}
            readOnly
          />
        );
      }}
      ifRejected={(err) => (
        <EmptyView
          title={
            // 404 error is expected when their is no data
            // for the selected area or link result
            // TODO: Instead this should be an empty response from the server
            toError(err).message.includes("404")
              ? t("study.outputs.noData")
              : t("data.error.matrix")
          }
          icon={GridOffIcon}
        />
      )}
    />
  );
}

export default OutputMatrix;
