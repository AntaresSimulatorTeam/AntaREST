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

import { useTranslation } from "react-i18next";
import { Box, Tooltip } from "@mui/material";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import Form from "../../../../../../../common/Form";
import { getStorage, type Storage, STORAGE_GROUPS, updateStorage } from "../utils";
import type { Area, StudyMetadata } from "@/types/types";
import { validateNumber } from "@/utils/validation/number";
import { useCallback } from "react";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import * as RA from "ramda-adjunct";

interface Props {
  study: StudyMetadata;
  areaId: Area["name"];
  storageId: Storage["id"];
}

function StorageForm({ study, areaId, storageId }: Props) {
  const { t } = useTranslation();
  const studyVersion = Number(study.version);

  // Prevents re-fetch while `useNavigateOnCondition` event occurs in parent component
  const defaultValues = useCallback(async () => {
    const storage = await getStorage(study.id, areaId, storageId);
    return {
      ...storage,
      // Convert to percentage ([0-1] -> [0-100])
      efficiency: storage.efficiency * 100,
      initialLevel: storage.initialLevel * 100,
    };
  }, []);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<Storage>) => {
    const newValues = { ...dirtyValues };
    // Convert to ratio ([0-100] -> [0-1])
    if (RA.isNumber(newValues.efficiency)) {
      newValues.efficiency /= 100;
    }
    if (RA.isNumber(newValues.initialLevel)) {
      newValues.initialLevel /= 100;
    }
    return updateStorage(study.id, areaId, storageId, newValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id + areaId}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      enableUndoRedo
      disableStickyFooter
      hideFooterDivider
    >
      {({ control }) => (
        <>
          <Fieldset legend={t("global.general")}>
            <StringFE label={t("global.name")} name="name" control={control} disabled />
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
          </Fieldset>
          <Fieldset legend={t("study.modelization.clusters.operatingParameters")}>
            {studyVersion >= 880 && (
              <SwitchFE
                label={t("global.enabled")}
                name="enabled"
                control={control}
                sx={{
                  alignItems: "center",
                  alignSelf: "center",
                }}
              />
            )}
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
              label={t("study.modelization.storages.efficiency")}
              name="efficiency"
              control={control}
              rules={{
                validate: validateNumber({ min: 0, max: 100 }),
              }}
            />
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
        </>
      )}
    </Form>
  );
}

export default StorageForm;
