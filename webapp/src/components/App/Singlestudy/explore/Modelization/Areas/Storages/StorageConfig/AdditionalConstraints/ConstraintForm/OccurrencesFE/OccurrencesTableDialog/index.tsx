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

import CustomScrollbar from "@/components/common/CustomScrollbar";
import DataGridForm, {
  type DataGridFormApi,
  type DataGridFormProps,
} from "@/components/common/DataGridForm";
import BasicDialog from "@/components/common/dialogs/BasicDialog";
import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import NumberFE from "@/components/common/fieldEditors/NumberFE";
import NumberSelectionsFE from "@/components/common/fieldEditors/NumberSelectionsFE";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import useConfirm from "@/hooks/useConfirm";
import type {
  AdditionalConstraint,
  AdditionalConstraintOccurrences,
} from "@/services/api/studies/areas/storages/types";
import { HOURS_IN } from "@/utils/date/constants";
import { Box, Button, ButtonGroup, Divider } from "@mui/material";
import * as R from "ramda";
import { useMemo, useRef, useState } from "react";
import { useWatch, type Control } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { validateOccurrences } from "../utils";
import ColumnsResize from "./ColumnsResize";
import {
  getOccurrencesCountFromGridData,
  getSelectedHoursByOccurrence,
  gridDataToOccurrences,
  occurrencesToGridData,
  resizeRow,
  type OccurrencesData,
} from "./utils";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  control: Control<AdditionalConstraint>;
  occurrences: AdditionalConstraintOccurrences;
  onEdit: (occurrences: AdditionalConstraintOccurrences) => void;
}

function OccurrencesTableDialog({ open, onClose, onEdit, control, occurrences }: Props) {
  const { t } = useTranslation();
  const [columnCount, setColumnCount] = useState(occurrences.length);
  const [offset, setOffset] = useState(0);
  const dataGridApiRef = useRef<DataGridFormApi<OccurrencesData>>(null);
  const [selectedHours, setSelectedHours] = useState<number[]>([]);
  const closeAction = useConfirm();
  const hasSelectedHours = selectedHours.length > 0;

  const name = useWatch({
    name: "name",
    control,
  });

  const columns = useMemo<DataGridFormProps["columns"]>(() => {
    return Array.from({ length: columnCount }, (_, index) => ({
      id: index.toString(),
      title: `${t("global.occurrence")} ${index + 1}`,
    }));
  }, [columnCount, t]);

  const defaultData = useMemo<OccurrencesData>(() => occurrencesToGridData(occurrences), []);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleOffsetChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(event.target.value);
    setOffset(R.clamp(0, HOURS_IN.WEEK - 1, value));
  };

  const handleResize = (value: number) => {
    if (dataGridApiRef.current) {
      const { data, setData } = dataGridApiRef.current;

      const resize = resizeRow(value);
      setData(R.map(resize, data));
    }
  };

  const handleDataChange = (data: OccurrencesData) => {
    setColumnCount(getOccurrencesCountFromGridData(data));
  };

  const handleSubmit = (
    { values }: SubmitHandlerPlus<OccurrencesData>,
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    // Prevent to submit the constraint form
    event.stopPropagation();

    const occurrences = gridDataToOccurrences(values);

    const validation = validateOccurrences(occurrences);
    if (validation !== true) {
      throw new Error(validation);
    }

    onEdit(occurrences);

    onClose();
  };

  const handleClose = async () => {
    if (dataGridApiRef.current?.formState.isDirty) {
      const isConfirmed = await closeAction.showConfirm();

      if (!isConfirmed) {
        return;
      }
    }

    onClose();
  };

  const handleUpdateHours = (updateFn: RA.Pred) => () => {
    if (dataGridApiRef.current) {
      const { data, setData } = dataGridApiRef.current;

      const selectedHoursByOccurrence = getSelectedHoursByOccurrence({
        hours: selectedHours,
        occurrencesCount: columnCount,
        offset,
      });

      const newData = R.mapObjIndexed((rowData, key) => {
        const hour = Number(key);

        return R.mapObjIndexed((active, key) => {
          const occurrenceIndex = Number(key);
          return selectedHoursByOccurrence[occurrenceIndex]?.includes(hour)
            ? updateFn(active)
            : active;
        }, rowData);
      }, data);

      setData(newData);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <BasicDialog
        title={t("study.modelization.storages.additionalConstraints.occurrences.dialog.title", {
          name,
        })}
        open={open}
        onClose={handleClose}
        fullScreen
      >
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1, overflow: "auto" }}>
          <Box>
            <CustomScrollbar>
              <Box sx={{ display: "flex", gap: 1, pt: 1 }}>
                <NumberSelectionsFE
                  label={t(
                    "study.modelization.storages.additionalConstraints.occurrences.dialog.hours",
                  )}
                  onChange={setSelectedHours}
                  maxNumber={HOURS_IN.WEEK}
                  size="extra-small"
                  sx={{ minWidth: 135 }}
                />
                <NumberFE
                  label={t("global.offset")}
                  value={offset}
                  onChange={handleOffsetChange}
                  disabled={!hasSelectedHours}
                  size="extra-small"
                  sx={{ width: 80, minWidth: 80 }}
                />
                <ButtonGroup disabled={!hasSelectedHours} color="secondary">
                  <Button onClick={handleUpdateHours(R.T)}>{t("global.enable")}</Button>
                  <Button onClick={handleUpdateHours(R.F)}>{t("global.disable")}</Button>
                  <Button onClick={handleUpdateHours(R.not)}>{t("global.reverse")}</Button>
                </ButtonGroup>
                <Divider flexItem orientation="vertical" />
                <ColumnsResize
                  key={columnCount}
                  defaultColumnCount={columnCount}
                  maxColumns={1000}
                  onResize={handleResize}
                />
              </Box>
            </CustomScrollbar>
          </Box>
          <DataGridForm
            columns={columns}
            defaultData={defaultData}
            onDataChange={handleDataChange}
            onSubmit={handleSubmit}
            extraActions={({ canSubmit }) => (
              <>
                <Button onClick={handleClose}>{t("global.close")}</Button>
                <Button type="submit" variant="contained" disabled={!canSubmit}>
                  {t("global.apply")}
                </Button>
              </>
            )}
            apiRef={dataGridApiRef}
            hideSubmitButton
            disableErrorSnackbar
          />
        </Box>
      </BasicDialog>
      <ConfirmationDialog
        open={closeAction.isPending}
        onConfirm={closeAction.yes}
        onCancel={closeAction.no}
        maxWidth="xs"
        alert="warning"
      >
        {t("form.changeNotSaved")}
      </ConfirmationDialog>
    </>
  );
}

export default OccurrencesTableDialog;
