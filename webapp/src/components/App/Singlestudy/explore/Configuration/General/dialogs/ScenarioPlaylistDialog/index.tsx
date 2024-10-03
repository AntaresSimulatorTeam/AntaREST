/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Box, Button, Divider } from "@mui/material";
import { useRef } from "react";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import Handsontable from "handsontable";
import { StudyMetadata } from "../../../../../../../../common/types";
import usePromise from "../../../../../../../../hooks/usePromise";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import TableForm from "../../../../../../../common/TableForm";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import {
  DEFAULT_WEIGHT,
  getPlaylist,
  PlaylistData,
  setPlaylist,
} from "./utils";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import {
  HandsontableProps,
  HotTableClass,
} from "../../../../../../../common/Handsontable";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

function ScenarioPlaylistDialog(props: Props) {
  const { study, open, onClose } = props;
  const { t } = useTranslation();
  const tableRef = useRef({} as HotTableClass);
  const res = usePromise(() => getPlaylist(study.id), [study.id]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdateStatus = (fn: RA.Pred) => () => {
    const api = tableRef.current.hotInstance;
    if (!api) {
      return;
    }

    const changes: Array<[number, string, boolean]> = api
      .getDataAtProp("status")
      .map((status, index) => [index, "status", fn(status)]);

    api.setDataAtRowProp(changes);
  };

  const handleResetWeights = () => {
    const api = tableRef.current.hotInstance as Handsontable;

    api.setDataAtRowProp(
      api.rowIndexMapper
        .getIndexesSequence()
        .map((rowIndex) => [rowIndex, "weight", DEFAULT_WEIGHT]),
    );
  };

  const handleSubmit = (data: SubmitHandlerPlus<PlaylistData>) => {
    return setPlaylist(study.id, data.values);
  };

  const handleCellsRender: HandsontableProps["cells"] = function cells(
    this,
    row,
    column,
    prop,
  ) {
    if (prop === "weight") {
      const status = this.instance.getDataAtRowProp(row, "status");
      return { readOnly: !status };
    }
    return {};
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("study.configuration.general.mcScenarioPlaylist")}
      open={open}
      onClose={onClose}
      actions={<Button onClick={onClose}>{t("global.close")}</Button>}
      // TODO: add `maxHeight` and `fullHeight` in BasicDialog`
      PaperProps={{ sx: { height: 500 } }}
      maxWidth="sm"
      fullWidth
    >
      <UsePromiseCond
        response={res}
        ifFulfilled={(defaultValues) => (
          <>
            <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1 }}>
              <Button color="secondary" onClick={handleUpdateStatus(R.T)}>
                {t(
                  "study.configuration.general.mcScenarioPlaylist.action.enableAll",
                )}
              </Button>
              <Button color="secondary" onClick={handleUpdateStatus(R.F)}>
                {t(
                  "study.configuration.general.mcScenarioPlaylist.action.disableAll",
                )}
              </Button>
              <Divider orientation="vertical" flexItem />
              <Button color="secondary" onClick={handleUpdateStatus(R.not)}>
                {t(
                  "study.configuration.general.mcScenarioPlaylist.action.reverse",
                )}
              </Button>
              <Divider orientation="vertical" flexItem />
              <Button color="secondary" onClick={handleResetWeights}>
                {t(
                  "study.configuration.general.mcScenarioPlaylist.action.resetWeights",
                )}
              </Button>
            </Box>
            <TableForm
              defaultValues={defaultValues}
              onSubmit={handleSubmit}
              sx={{ pt: 2, overflow: "auto" }}
              tableProps={{
                rowHeaders: (row) => `MC Year ${row.id}`,
                tableRef,
                stretchH: "all",
                className: "htCenter",
                cells: handleCellsRender,
              }}
            />
          </>
        )}
      />
    </BasicDialog>
  );
}

export default ScenarioPlaylistDialog;
