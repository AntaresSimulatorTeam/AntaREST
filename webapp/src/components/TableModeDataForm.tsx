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
import usePromise from "@/hooks/usePromise";
import { getTableModeData, setTableModeData } from "@/services/api/studies/tableMode";
import type { TableModeData } from "@/services/api/studies/tableMode/types";
import type { Study } from "@/services/api/studies/types";
import type { TableModeColumnsForType, TableModeType } from "@/services/api/tablemode/types";
import type { GridColumn } from "@glideapps/glide-data-grid";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Box, Typography } from "@mui/material";
import startCase from "lodash/startCase";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import DataGridForm, { type DataGridFormProps } from "./DataGridForm";
import type { SubmitHandlerPlus } from "./Form/types";
import EmptyView from "./page/EmptyView";
import UsePromiseCond from "./utils/UsePromiseCond";

export interface TableModeDataFormProps<T extends TableModeType = TableModeType> {
  studyId: Study["id"];
  type: T;
  columns: TableModeColumnsForType<T>;
  name?: string;
  extraActions?: DataGridFormProps["extraActions"];
}

function TableModeDataForm<T extends TableModeType>({
  studyId,
  type,
  columns,
  name,
  extraActions,
}: TableModeDataFormProps<T>) {
  const { t } = useTranslation();
  const [gridColumns, setGridColumns] = useState<DataGridFormProps<TableModeData>["columns"]>([]);
  const columnsDep = columns.join(",");

  const res = usePromise(
    () => getTableModeData({ studyId, tableType: type, columns }),
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

  const handleSubmit = (data: SubmitHandlerPlus<TableModeData>) => {
    return setTableModeData({ studyId, tableType: type, data: data.dirtyValues });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: 1 }}>
      {name && (
        <Typography color="textSecondary" gutterBottom noWrap>
          {name}
        </Typography>
      )}
      <UsePromiseCond
        response={res}
        ifPending={() => <DataGridSkeleton />}
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
              title={t("study.outputs.noData")}
              secondaryActions={
                typeof extraActions === "function"
                  ? extraActions({ canSubmit: false })
                  : extraActions
              }
            />
          )
        }
      />
    </Box>
  );
}

export default TableModeDataForm;
