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
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../common/Form";
import { STORAGE_GROUPS, type Storage } from "./utils";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../../common/types";
import { validateNumber } from "@/utils/validation/number";

function Fields() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { control } = useFormContextPlus<Storage>();
  const studyVersion = parseInt(study.version, 10);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
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
  );
}

export default Fields;
