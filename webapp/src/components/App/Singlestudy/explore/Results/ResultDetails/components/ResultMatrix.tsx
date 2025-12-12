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
import type {
  DateTimes,
  EnhancedGridColumn,
  ResultMatrixDTO,
} from "@/components/common/Matrix/shared/types";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import type { MatrixIndex } from "@/types/types";
import { toError } from "../../../../../../../utils/fnUtils";
import FilterableMatrixGrid, {
  type FilterableMatrixGridHandle,
} from "../../../../../../common/Matrix/components/FilterableMatrixGrid";
import { isNonEmptyMatrix } from "../../../../../../common/Matrix/shared/types";
import EmptyView from "../../../../../../common/page/EmptyView";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";

interface ResultMatrixProps {
  matrixRes: UsePromiseResponse<ResultMatrixDTO | undefined>;
  resultColHeaders: string[][];
  filteredData: number[][];
  resultColumns: EnhancedGridColumn[];
  matrixGridRef: React.RefObject<FilterableMatrixGridHandle>;
  dateTime: DateTimes | undefined;
  dateTimeMetadata: MatrixIndex | undefined;
}

function ResultMatrix({
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
      ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
      ifFulfilled={() => {
        if (resultColHeaders.length === 0) {
          return <Skeleton sx={{ height: 1, transform: "none" }} />;
        }

        if (!isNonEmptyMatrix(filteredData)) {
          return <EmptyView title={t("study.results.noData")} icon={GridOffIcon} />;
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
              ? t("study.results.noData")
              : t("data.error.matrix")
          }
          icon={GridOffIcon}
        />
      )}
    />
  );
}

export default ResultMatrix;
