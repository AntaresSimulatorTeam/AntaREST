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
import StringFE from "@/components/common/fieldEditors/StringFE";
import Fieldset from "@/components/common/Fieldset";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import { copyStudy } from "@/services/api/studies";
import type { StudyMetadata } from "@/types/types";
import { validateString } from "@/utils/validation/string";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { useTranslation } from "react-i18next";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

const defaultValues = {
  studyName: "",
};

function CopyStudyDialog({ study, open, onClose }: Props) {
  const { t } = useTranslation();
  const defaultStudyName = `${study.name} (${t("studies.copySuffix")})`;

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values: { studyName } }: SubmitHandlerPlus<typeof defaultValues>) => {
    return copyStudy({
      studyId: study.id,
      studyName: studyName || defaultStudyName,
      withOutputs: false,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={t("study.copy")}
      titleIcon={ContentCopyIcon}
      maxWidth="sm"
      submitButtonIcon={null}
      onCancel={onClose}
      onSubmit={handleSubmit}
      onSubmitSuccessful={onClose}
      config={{ defaultValues }}
      allowSubmitOnPristine
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            name="studyName"
            label={t("global.name")}
            control={control}
            placeholder={defaultStudyName}
            rules={{
              validate: validateString({ allowEmpty: true }),
            }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CopyStudyDialog;
