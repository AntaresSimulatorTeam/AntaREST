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

import { Button, ButtonGroup, Divider } from "@mui/material";
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import type * as RA from "ramda-adjunct";
import type { StudyMetadata } from "../../../../../../../types/types";
import usePromise from "../../../../../../../hooks/usePromise";
import BasicDialog from "../../../../../../common/dialogs/BasicDialog";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";
import type { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import DataGridForm, {
  type DataGridFormApi,
  type DataGridFormState,
} from "@/components/common/DataGridForm";
import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import useConfirm from "@/hooks/useConfirm";
import type { PlaylistData } from "@/services/api/studies/config/playlist/types";
import { getPlaylistData, setPlaylistData } from "@/services/api/studies/config/playlist";
import { DEFAULT_WEIGHT } from "@/services/api/studies/config/playlist/constants";

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
      PaperProps={{ sx: { height: 700 } }}
      maxWidth="md"
      fullWidth
    >
      <UsePromiseCond
        response={res}
        ifFulfilled={(defaultValues) => (
          <>
            <ButtonGroup disabled={isSubmitting} sx={{ justifyContent: "flex-end", mb: 1 }}>
              <Button color="secondary" onClick={handleUpdateStatus(R.T)}>
                {t("study.configuration.general.mcScenarioPlaylist.action.enableAll")}
              </Button>
              <Button color="secondary" onClick={handleUpdateStatus(R.F)}>
                {t("study.configuration.general.mcScenarioPlaylist.action.disableAll")}
              </Button>
              <Divider orientation="vertical" flexItem />
              <Button color="secondary" onClick={handleUpdateStatus(R.not)}>
                {t("study.configuration.general.mcScenarioPlaylist.action.reverse")}
              </Button>
              <Divider orientation="vertical" flexItem />
              <Button color="secondary" onClick={handleResetWeights}>
                {t("study.configuration.general.mcScenarioPlaylist.action.resetWeights")}
              </Button>
            </ButtonGroup>
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
          </>
        )}
      />
    </BasicDialog>
  );
}

export default ScenarioPlaylistDialog;
