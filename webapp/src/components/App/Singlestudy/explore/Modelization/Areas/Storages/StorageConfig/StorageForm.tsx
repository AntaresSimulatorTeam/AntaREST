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

import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import type { Area, StudyMetadata } from "@/types/types";
import { validateNumber } from "@/utils/validation/number";
import { Box, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import Fieldset from "../../../../../../../common/Fieldset";
import Form from "../../../../../../../common/Form";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import {
  convertPercentageToRatio,
  convertRatioToPercentage,
  type FormalizedStorage,
  getStorage,
  type Storage,
  STORAGE_GROUPS,
  updateStorage,
} from "../utils";

interface Props {
  study: StudyMetadata;
  areaId: Area["name"];
  storageId: Storage["id"];
}

function StorageForm({ study, areaId, storageId }: Props) {
  const { t } = useTranslation();
  const studyVersion = Number(study.version);

  ////////////////////////////////////////////////////////////////
  // Config
  ////////////////////////////////////////////////////////////////

  const getDefaultValues = async () => {
    const storage = await getStorage(study.id, areaId, storageId);
    return convertRatioToPercentage(storage);
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ dirtyValues }: SubmitHandlerPlus<FormalizedStorage>) => {
    const updatedStorage = await updateStorage(
      study.id,
      areaId,
      storageId,
      convertPercentageToRatio(dirtyValues),
    );

    return convertRatioToPercentage(updatedStorage);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id + areaId + storageId}
      config={{ defaultValues: getDefaultValues }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      {({ control }) => (
        <>
          <Fieldset legend={t("study.modelization.clusters.operatingParameters")}>
            <StringFE label={t("global.name")} name="name" control={control} disabled />
            {studyVersion < 920 ? (
              <SelectFE
                label={t("global.group")}
                name="group"
                control={control}
                options={STORAGE_GROUPS}
                startCaseLabel={false}
                sx={{
                  alignSelf: "center",
                }}
              />
            ) : (
              <StringFE
                label={t("global.group")}
                name="group"
                datalist={STORAGE_GROUPS}
                control={control}
              />
            )}
            {studyVersion >= 880 && (
              <SwitchFE label={t("global.enabled")} name="enabled" control={control} />
            )}
            <Fieldset.Break />
            <Tooltip
              title={t("study.modelization.storages.reservoirCapacity.info")}
              arrow
              placement="top"
            >
              <Box>
                <NumberFE
                  label={t("study.modelization.storages.reservoirCapacity")}
                  name="reservoirCapacity"
                  control={control}
                  rules={{
                    validate: validateNumber({ min: 0 }),
                  }}
                />
              </Box>
            </Tooltip>
            <NumberFE
              label={t("study.modelization.storages.initialLevel")}
              name="initialLevel"
              control={control}
              rules={{
                validate: validateNumber({ min: 0, max: 100 }),
              }}
            />
            <SwitchFE
              label={t("study.modelization.storages.initialLevelOptim")}
              name="initialLevelOptim"
              control={control}
              sx={{
                alignItems: "center",
                alignSelf: "center",
                width: 2,
              }}
            />
          </Fieldset>
          <Fieldset legend={t("study.modelization.storages.injectionParameters")}>
            <Tooltip
              title={t("study.modelization.storages.injectionNominalCapacity.info")}
              arrow
              placement="top"
            >
              <Box>
                <NumberFE
                  label={t("study.modelization.storages.injectionNominalCapacity")}
                  name="injectionNominalCapacity"
                  control={control}
                  rules={{
                    validate: validateNumber({ min: 0 }),
                  }}
                />
              </Box>
            </Tooltip>
            <NumberFE
              label={t("study.modelization.storages.efficiency")}
              name="efficiency"
              control={control}
              rules={{
                validate: validateNumber({ min: 0, max: 100 }),
              }}
            />
            {studyVersion >= 920 && (
              <SwitchFE
                label={t("study.modelization.storages.penalizeVariationInjection")}
                name="penalizeVariationInjection"
                control={control}
              />
            )}
          </Fieldset>
          <Fieldset legend={t("study.modelization.storages.withdrawalParameters")}>
            <Tooltip
              title={t("study.modelization.storages.withdrawalNominalCapacity.info")}
              arrow
              placement="top"
            >
              <Box>
                <NumberFE
                  label={t("study.modelization.storages.withdrawalNominalCapacity")}
                  name="withdrawalNominalCapacity"
                  control={control}
                  rules={{
                    validate: validateNumber({ min: 0 }),
                  }}
                />
              </Box>
            </Tooltip>
            {studyVersion >= 920 && (
              <>
                <Tooltip
                  title={t("study.modelization.storages.efficiencyWithdrawal.info")}
                  arrow
                  placement="top"
                >
                  <Box>
                    <NumberFE
                      label={t("study.modelization.storages.efficiencyWithdrawal")}
                      name="efficiencyWithdrawal"
                      control={control}
                      rules={{
                        validate: validateNumber({ min: 0, max: 100 }),
                      }}
                    />
                  </Box>
                </Tooltip>
                <SwitchFE
                  label={t("study.modelization.storages.penalizeVariationWithdrawal")}
                  name="penalizeVariationWithdrawal"
                  control={control}
                />
              </>
            )}
          </Fieldset>
        </>
      )}
    </Form>
  );
}

export default StorageForm;
