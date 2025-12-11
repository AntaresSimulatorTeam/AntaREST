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

import FormDialog from "@/components/dialogs/FormDialog";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { launchStudy } from "@/services/api/launcher/index";
import type { LauncherParams } from "@/services/api/launcher/types";
import type { StudyMetadata } from "@/types/types";
import BoltIcon from "@mui/icons-material/Bolt";
import { useTranslation } from "react-i18next";
import Fields from "./Fields";
import LauncherMetrics from "./LauncherMetrics";
import StudyList from "./StudyList";
import { getDefaultValues, type FormValues } from "./utils";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  studyIds: Array<StudyMetadata["id"]>;
}

function StudyLaunchDialog({ open, onClose, studyIds }: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<FormValues>) => {
    const hasConfig = values.configuration !== "";

    const launcherParams: LauncherParams = {
      outputSuffix: values.name,
      otherOptions: hasConfig ? undefined : values.otherOptions,
      autoUnzip: values.autoUnzip,
      // Note: fields can be set event if Xpansion is disabled.
      // This can happen with the default values.
      xpansion: values.xpansion
        ? {
            enabled: true,
            adequacyCriterion: values.adequacyCriterion,
            sensitivityMode: values.sensitivityMode,
            // `output_id` has to be provided only if `sensitivity_mode` is enabled.
            outputId: values.sensitivityMode ? values.output : undefined,
          }
        : { enabled: false },
      nbCores: values.nbCores,
    };

    return Promise.all(
      studyIds.map((id) =>
        launchStudy({
          studyId: id,
          launcherId: values.launcher,
          solverPresetsId: hasConfig ? values.configuration : undefined,
          launcherParams,
          version: values.version,
        }),
      ),
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={t("launcher.dialog.title", { count: studyIds.length })}
      titleIcon={BoltIcon}
      config={{ defaultValues: () => getDefaultValues(studyIds) }}
      onCancel={onClose}
      submitButtonText={t("global.launch")}
      submitButtonIcon={<BoltIcon />}
      maxWidth="md"
      onSubmit={handleSubmit}
      onSubmitSuccessful={onClose}
      allowSubmitOnPristine
    >
      <StudyList studyIds={studyIds} />
      <Fields />
      <LauncherMetrics />
    </FormDialog>
  );
}

export default StudyLaunchDialog;
