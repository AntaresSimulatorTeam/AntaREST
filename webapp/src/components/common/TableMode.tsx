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

import { useEffect, useState } from "react";
import type { StudyMetadata } from "../../types/types";
import usePromise from "../../hooks/usePromise";
import { getTableMode, setTableMode } from "../../services/api/studies/tableMode";
import type {
  TableData,
  TableModeColumnsForType,
  TableModeType,
} from "../../services/api/studies/tableMode/types";
import type { SubmitHandlerPlus } from "./Form/types";
import UsePromiseCond from "./utils/UsePromiseCond";
import GridOffIcon from "@mui/icons-material/GridOff";
import EmptyView from "./page/EmptyView";
import { useTranslation } from "react-i18next";
import DataGridForm, { type DataGridFormProps } from "./DataGridForm";
import startCase from "lodash/startCase";
import type { GridColumn } from "@glideapps/glide-data-grid";

export interface TableModeProps<T extends TableModeType = TableModeType> {
  studyId: StudyMetadata["id"];
  type: T;
  columns: TableModeColumnsForType<T>;
  extraActions?: React.ReactNode;
}

function TableMode<T extends TableModeType>({
  studyId,
  type,
  columns,
  extraActions,
}: TableModeProps<T>) {
  const { t } = useTranslation();
  const [gridColumns, setGridColumns] = useState<DataGridFormProps<TableData>["columns"]>([]);
  const columnsDep = columns.join(",");

  const res = usePromise(
    () => getTableMode({ studyId, tableType: type, columns }),
    [studyId, type, columnsDep],
  );

  // Filter columns based on the data received, because the API may return
  // fewer columns than requested depending on the study root
  useEffect(() => {
    const data = res.data || {};
    const rowNames = Object.keys(data);

    if (rowNames.length === 0) {
      setGridColumns([]);
      return;
    }

    const columnNames = Object.keys(data[rowNames[0]]);

    setGridColumns(
      columns
        .filter((col) => columnNames.includes(col))
        .map((col) => {
          const title = startCase(col);
          return {
            title,
            id: col,
          } satisfies GridColumn;
        }),
    );
  }, [res.data, columnsDep]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<TableData>) => {
    return setTableMode({ studyId, tableType: type, data: data.dirtyValues });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifFulfilled={(data) =>
        gridColumns.length > 0 ? (
          <DataGridForm
            defaultData={data}
            columns={gridColumns}
            onSubmit={handleSubmit}
            extraActions={extraActions}
          />
        ) : (
          <EmptyView
            icon={GridOffIcon}
            title={t("study.results.noData")}
            extraActions={extraActions}
          />
        )
      }
    />
  );
}

export default TableMode;
