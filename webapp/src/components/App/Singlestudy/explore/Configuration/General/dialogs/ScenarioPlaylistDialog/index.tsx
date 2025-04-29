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

import CustomScrollbar from "@/components/common/CustomScrollbar";
import DataGridForm, {
  type DataGridFormApi,
  type DataGridFormState,
} from "@/components/common/DataGridForm";
import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import useConfirm from "@/hooks/useConfirm";
import { getPlaylistData, setPlaylistData } from "@/services/api/studies/config/playlist";
import { DEFAULT_WEIGHT } from "@/services/api/studies/config/playlist/constants";
import type { PlaylistData } from "@/services/api/studies/config/playlist/types";
import { Box, Button, ButtonGroup } from "@mui/material";
import * as R from "ramda";
import type * as RA from "ramda-adjunct";
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import usePromise from "../../../../../../../../hooks/usePromise";
import type { StudyMetadata } from "../../../../../../../../types/types";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import YearsSelectionFE from "./YearsSelectionFE";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

function ScenarioPlaylistDialog(props: Props) {
  const { study, open, onClose } = props;
  const { t } = useTranslation();
  const dataGridApiRef = useRef<DataGridFormApi<PlaylistData>>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const closeAction = useConfirm();
  const res = usePromise(() => getPlaylistData({ studyId: study.id }), [study.id]);

  const columns = useMemo(() => {
    return [
      {
        id: "status" as const,
        title: t("global.status"),
        grow: 1,
      },
      {
        id: "weight" as const,
        title: t("global.weight"),
        grow: 1,
      },
    ];
  }, [t]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdateStatus = (fn: RA.Pred) => () => {
    if (dataGridApiRef.current) {
      const { data, setData } = dataGridApiRef.current;
      setData(R.map(R.evolve({ status: fn }), data));
    }
  };

  const handleResetWeights = () => {
    if (dataGridApiRef.current) {
      const { data, setData } = dataGridApiRef.current;
      setData(R.map(R.assoc("weight", DEFAULT_WEIGHT), data));
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
      fullWidth
      sx={{ ".MuiDialogContent-root": { pb: 0 } }}
    >
      <UsePromiseCond
        response={res}
        ifFulfilled={(defaultValues) => (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1, overflow: "auto" }}>
            <Box>
              <CustomScrollbar>
                <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                  <YearsSelectionFE />
                  <ButtonGroup disabled={isSubmitting} color="secondary" size="extra-small">
                    <Button onClick={handleUpdateStatus(R.T)}>
                      {t("study.configuration.general.mcScenarioPlaylist.action.enableAll")}
                    </Button>
                    <Button onClick={handleUpdateStatus(R.F)}>
                      {t("study.configuration.general.mcScenarioPlaylist.action.disableAll")}
                    </Button>
                    <Button onClick={handleUpdateStatus(R.not)}>
                      {t("study.configuration.general.mcScenarioPlaylist.action.reverse")}
                    </Button>
                    <Button onClick={handleResetWeights}>
                      {t("study.configuration.general.mcScenarioPlaylist.action.resetWeights")}
                    </Button>
                  </ButtonGroup>
                </Box>
              </CustomScrollbar>
            </Box>
            <DataGridForm
              defaultData={defaultValues}
              columns={columns}
              rowMarkers={{
                kind: "clickable-string",
                getTitle: (index) => `MC Year ${index + 1}`,
              }}
              onSubmit={handleSubmit}
              onStateChange={handleFormStateChange}
              apiRef={dataGridApiRef}
              enableColumnResize={false}
            />
            <ConfirmationDialog
              open={closeAction.isPending}
              onConfirm={closeAction.yes}
              onCancel={closeAction.no}
              maxWidth="xs"
              alert="warning"
            >
              {t("form.changeNotSaved")}
            </ConfirmationDialog>
          </Box>
        )}
      />
    </BasicDialog>
  );
}

export default ScenarioPlaylistDialog;
