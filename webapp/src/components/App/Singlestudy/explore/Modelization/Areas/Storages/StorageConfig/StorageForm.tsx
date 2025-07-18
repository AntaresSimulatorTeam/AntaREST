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
import type { Area, StudyMetadata } from "@/types/types";
import { validateNumber } from "@/utils/validation/number";
import { Box, Tooltip } from "@mui/material";
import * as RA from "ramda-adjunct";
import { useTranslation } from "react-i18next";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import Form from "../../../../../../../common/Form";
import {
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
    const { efficiency, efficiencyWithdrawal, initialLevel, ...rest } = await getStorage(
      study.id,
      areaId,
      storageId,
    );

    return {
      ...rest,
      // Convert to percentage ([0-1] -> [0-100])
      efficiency: efficiency * 100,
      efficiencyWithdrawal: efficiencyWithdrawal * 100,
      initialLevel: initialLevel * 100,
    };
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<FormalizedStorage>) => {
    const newValues = { ...dirtyValues };
    // Convert to ratio ([0-100] -> [0-1])
    if (RA.isNumber(newValues.efficiency)) {
      newValues.efficiency /= 100;
    }
    if (RA.isNumber(newValues.initialLevel)) {
      newValues.initialLevel /= 100;
    }
    if (RA.isNumber(newValues.efficiencyWithdrawal)) {
      newValues.efficiencyWithdrawal /= 100;
    }
    return updateStorage(study.id, areaId, storageId, newValues);
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
      disableStickyFooter
      hideFooterDivider
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
