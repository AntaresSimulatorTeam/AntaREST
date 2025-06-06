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

import UpgradeIcon from "@mui/icons-material/Upgrade";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getStudyVersionsFormatted } from "../../../../../redux/selectors";
import { upgradeStudy } from "../../../../../services/api/study";
import type { StudyMetadata } from "../../../../../types/types";
import Fieldset from "../../../../common/Fieldset";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";
import FormDialog from "../../../../common/dialogs/FormDialog";
import SelectFE from "../../../../common/fieldEditors/SelectFE";

interface Props {
  study: StudyMetadata;
  onClose: VoidFunction;
  open: boolean;
}

const defaultValues = {
  version: "",
};

function UpgradeDialog({ study, onClose, open }: Props) {
  const { t } = useTranslation();
  const versions = useAppSelector(getStudyVersionsFormatted);

  const versionOptions = useMemo(() => {
    return versions
      .filter((version) => version.id > study.version)
      .sort((a, b) => b.name.localeCompare(a.name))
      .map(({ id, name }) => ({
        value: id,
        label: name,
      }));
  }, [versions, study.version]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { version } }: SubmitHandlerPlus<typeof defaultValues>) => {
    return upgradeStudy(study.id, version);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.upgrade")}
      titleIcon={UpgradeIcon}
      submitButtonIcon={null}
      submitButtonText={t("study.upgrade")}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      onSubmitSuccessful={onClose}
      config={{ defaultValues }}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <SelectFE name="version" label="Version" options={versionOptions} control={control} />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default UpgradeDialog;
