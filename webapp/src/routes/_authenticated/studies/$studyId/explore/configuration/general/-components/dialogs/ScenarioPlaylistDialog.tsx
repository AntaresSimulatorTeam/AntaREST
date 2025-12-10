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

import CustomScrollbar from "@/components/CustomScrollbar";
import DataGridForm, {
  type DataGridFormApi,
  type DataGridFormProps,
  type DataGridFormState,
} from "@/components/DataGridForm";
import BasicDialog from "@/components/dialogs/BasicDialog";
import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import NumberSelectionsFE from "@/components/fieldEditors/NumberSelectionsFE";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import useConfirm from "@/hooks/useConfirm";
import { getPlaylistData, setPlaylistData } from "@/services/api/studies/config/playlist";
import { DEFAULT_WEIGHT } from "@/services/api/studies/config/playlist/constants";
import type { Playlist, PlaylistData } from "@/services/api/studies/config/playlist/types";
import { appendColon } from "@/utils/i18nUtils";
import { selectionToNumbers } from "@/utils/numberSelectionsUtils";
import { Box, Button, ButtonGroup } from "@mui/material";
import { Decimal } from "decimal.js-light";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import usePromise from "../../../../../../../../../hooks/usePromise";
import type { StudyMetadata } from "../../../../../../../../../types/types";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

const getMaxYear = (data: PlaylistData) => Object.keys(data).length;

function ScenarioPlaylistDialog({ study, open, onClose }: Props) {
  const { t } = useTranslation();
  const dataGridApiRef = useRef<DataGridFormApi<PlaylistData>>(null);
  const [selectedYears, setSelectedYears] = useState<number[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [totals, setTotals] = useState({ selected: 0, sumWeights: 0 });
  const closeAction = useConfirm();
  const res = usePromise(() => getPlaylistData({ studyId: study.id }), {
    deps: [study.id],
    onDataChange: handleFetchDataChange,
  });
  const disableActions = selectedYears.length === 0 || isSubmitting;

  const columns = useMemo<DataGridFormProps<PlaylistData>["columns"]>(() => {
    return [
      {
        id: "status" as const,
        title: t("global.status"),
        grow: 1,
        trailingRowOptions: {
          hint: `${appendColon(t("study.configuration.general.mcScenarioPlaylist.totalSelected.label"))} ${totals.selected}`,
        },
      },
      {
        id: "weight" as const,
        title: t("global.weight"),
        grow: 1,
        trailingRowOptions: {
          hint: `${appendColon(t("study.configuration.general.mcScenarioPlaylist.totalWeight.label"))} ${totals.sumWeights}`,
        },
      },
    ];
  }, [t, totals]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const mapSelectedYears = (fn: (item: Playlist) => Playlist, data: PlaylistData): PlaylistData => {
    if (selectedYears.length === 0) {
      return data;
    }

    return RA.mapIndexed((item, index) => {
      if (selectedYears.includes(index + 1)) {
        return fn(item);
      }
      return item;
    }, data);
  };

  function updateTotals(data: PlaylistData) {
    const newTotals = Object.entries(data).reduce(
      (acc, [_, { status, weight }]) => {
        if (status) {
          acc.selected += 1;
          // Vanilla JS has imprecision with floats, so we use Decimal.js to handle it
          acc.sumWeights = new Decimal(acc.sumWeights).plus(weight).toNumber();
        }
        return acc;
      },
      { selected: 0, sumWeights: 0 },
    );

    setTotals(newTotals);
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  function handleFetchDataChange(data?: PlaylistData) {
    if (!data) {
      return;
    }

    updateTotals(data);

    const maxYear = getMaxYear(data);
    setSelectedYears(maxYear > 0 ? selectionToNumbers([1, maxYear]) : []);
  }

  const handleUpdateStatus = (updateFn: RA.Pred) => () => {
    if (dataGridApiRef.current) {
      const { data, setData } = dataGridApiRef.current;
      setData(mapSelectedYears(R.evolve({ status: updateFn }), data));
    }
  };

  const handleResetWeights = () => {
    if (dataGridApiRef.current) {
      const { data, setData } = dataGridApiRef.current;
      setData(mapSelectedYears(R.assoc("weight", DEFAULT_WEIGHT), data));
    }
  };

  const handleSubmit = (data: SubmitHandlerPlus<PlaylistData>) => {
    return setPlaylistData({ studyId: study.id, data: data.values });
  };

  const handleClose = () => {
    if (isSubmitting) {
      return;
    }

    if (isDirty) {
      return closeAction.showConfirm().then((confirm) => {
        if (confirm) {
          onClose();
        }
      });
    }

    onClose();
  };

  const handleFormStateChange = (formState: DataGridFormState) => {
    setIsSubmitting(formState.isSubmitting);
    setIsDirty(formState.isDirty);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("study.configuration.general.mcScenarioPlaylist")}
      open={open}
      onClose={handleClose}
      actions={
        <Button onClick={handleClose} disabled={isSubmitting}>
          {t("global.close")}
        </Button>
      }
      maxWidth="md"
      sx={{ ".MuiDialogContent-root": { pb: 0 } }}
    >
      <UsePromiseCond
        response={res}
        ifFulfilled={(defaultData) => (
          <>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1, overflow: "auto" }}>
              <Box>
                <CustomScrollbar>
                  <Box sx={{ display: "flex", gap: 1, pt: 1 }}>
                    <NumberSelectionsFE
                      defaultValue={selectedYears}
                      label={t("study.configuration.general.mcScenarioPlaylist.scenarios")}
                      onChange={setSelectedYears}
                      maxNumber={getMaxYear(defaultData)}
                      size="extra-small"
                      sx={{ minWidth: 135 }}
                    />
                    <ButtonGroup disabled={disableActions} color="secondary">
                      <Button onClick={handleUpdateStatus(R.T)}>{t("global.enable")}</Button>
                      <Button onClick={handleUpdateStatus(R.F)}>{t("global.disable")}</Button>
                      <Button onClick={handleUpdateStatus(R.not)}>{t("global.reverse")}</Button>
                      <Button onClick={handleResetWeights}>
                        {t("study.configuration.general.mcScenarioPlaylist.action.resetWeights")}
                      </Button>
                    </ButtonGroup>
                  </Box>
                </CustomScrollbar>
              </Box>
              <DataGridForm
                defaultData={defaultData}
                columns={columns}
                rowMarkers={{
                  kind: "clickable-string",
                  getTitle: (index) => `MC Year ${index + 1}`,
                }}
                onSubmit={handleSubmit}
                onDataChange={updateTotals}
                onStateChange={handleFormStateChange}
                apiRef={dataGridApiRef}
                enableColumnResize={false}
                trailingRowOptions={{
                  sticky: true,
                  addIcon: "",
                }}
                onRowAppended={() => {
                  // Allow to display the trailing row, used to display the totals.
                  // This is the only way to have a footer in the DataGridForm.
                }}
              />
            </Box>
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
        )}
      />
    </BasicDialog>
  );
}

export default ScenarioPlaylistDialog;
