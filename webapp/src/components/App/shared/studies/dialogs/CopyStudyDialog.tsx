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
import FieldSkeleton from "@/components/common/fieldEditors/FieldSkeleton";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import Fieldset from "@/components/common/Fieldset";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import UsePromiseCond from "@/components/common/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import { copyStudy } from "@/services/api/studies";
import { getStudyOutputs } from "@/services/api/study";
import type { StudyMetadata, StudyOutput } from "@/types/types";
import { validateStudyName } from "@/utils/studiesUtils";
import FileCopyOutlinedIcon from "@mui/icons-material/FileCopyOutlined";
import SaveAsIcon from "@mui/icons-material/SaveAs";
import { Box, Chip } from "@mui/material";
import { useTranslation } from "react-i18next";
import StudyPathFE from "../StudyPathFE";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

interface DefaultValues {
  studyName: string;
  destinationFolder: string;
  outputIds?: Array<StudyOutput["name"]>;
}

function CopyStudyDialog({ study, open, onClose }: Props) {
  const { t } = useTranslation();
  const isVariant = study.type === "variantstudy";
  const Icon = isVariant ? SaveAsIcon : FileCopyOutlinedIcon;

  const outputsRes = usePromise(async () => {
    const outputs = await getStudyOutputs(study.id);
    return outputs.map(({ name }) => name);
  }, [study.id]);

  const defaultValues: DefaultValues = {
    studyName: `${study.name} (${t("studies.copySuffix")})`,
    destinationFolder: "",
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({
    values: { studyName, destinationFolder, outputIds = [] },
  }: SubmitHandlerPlus<DefaultValues>) => {
    return copyStudy({
      studyId: study.id,
      studyName: studyName.trim(),
      destinationFolder,
      outputIds,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={isVariant ? t("study.copyVariant") : t("global.copy")}
      titleIcon={Icon}
      maxWidth="sm"
      submitButtonIcon={<Icon />}
      submitButtonText={isVariant ? t("global.record") : t("global.copy")}
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
            rules={{ validate: validateStudyName }}
            autoFocus
          />
          <StudyPathFE name="destinationFolder" control={control} />
          <UsePromiseCond
            response={outputsRes}
            ifPending={() => (
              <FieldSkeleton>
                <SelectFE options={[]} />
              </FieldSkeleton>
            )}
            ifRejected={() => (
              <SelectFE options={[]} helperText={t("study.error.listOutputs")} error disabled />
            )}
            ifFulfilled={(outputs) => (
              <SelectFE
                name="outputIds"
                label={t("global.outputs")}
                control={control}
                defaultValue={outputs}
                options={outputs}
                startCaseLabel={false}
                multiple
                renderValue={(selected) => {
                  if (Array.isArray(selected)) {
                    return (
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    );
                  }
                }}
              />
            )}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CopyStudyDialog;
