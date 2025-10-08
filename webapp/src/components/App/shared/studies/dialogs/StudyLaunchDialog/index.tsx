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

import FormDialog from "@/components/common/dialogs/FormDialog";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import { launchStudy } from "@/services/api/study";
import type { LaunchOptions, StudyMetadata } from "@/types/types";
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
    const {
      name,
      version,
      otherOptions,
      autoUnzip,
      xpansion,
      sensitivityMode,
      output,
      launcher,
      nbCores,
    } = values;

    const options: LaunchOptions = {
      output_suffix: name,
      other_options: otherOptions,
      auto_unzip: autoUnzip,
      xpansion: {
        enabled: xpansion,
        sensitivity_mode: sensitivityMode,
        output_id: output,
      },
      nb_cpu: nbCores,
    };

    return Promise.all(studyIds.map((id) => launchStudy(id, options, version, launcher)));
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
