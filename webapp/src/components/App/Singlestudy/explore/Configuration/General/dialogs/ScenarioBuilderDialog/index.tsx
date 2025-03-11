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

import { TabContext, TabList, TabPanel, type TabListProps } from "@mui/lab";
import { Box, Button, Tab, Skeleton } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../../../types/types";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import Table from "./Table";
import { getScenarioConfigByType, SCENARIOS, type ScenarioType } from "./utils";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import withAreas from "./withAreas";
import usePromiseWithSnackbarError from "../../../../../../../../hooks/usePromiseWithSnackbarError";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

// HOC that provides areas menu, for particular cases. (e.g thermals)
const EnhancedTable = withAreas(Table);

function ScenarioBuilderDialog({ study, open, onClose }: Props) {
  const { t } = useTranslation();
  const [selectedScenario, setSelectedScenario] = useState<ScenarioType>(SCENARIOS[0]);

  const config = usePromiseWithSnackbarError(
    () => getScenarioConfigByType(study.id, selectedScenario),
    {
      errorMessage: t("study.configuration.general.mcScenarioBuilder.noConfig.error"),
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleScenarioChange: TabListProps["onChange"] = (_, type) => {
    setSelectedScenario(type);
    config.reload();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("study.configuration.general.mcScenarioBuilder")}
      open={open}
      onClose={onClose}
      actions={<Button onClick={onClose}>{t("global.close")}</Button>}
      maxWidth="xl"
      fullWidth
      contentProps={{
        sx: { p: 1, height: "95vh", width: 1 },
      }}
    >
      <TabContext value={selectedScenario}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList onChange={handleScenarioChange}>
            {SCENARIOS.map((type) => (
              <Tab
                key={type}
                value={type}
                label={t(`study.configuration.general.mcScenarioBuilder.tab.${type}`)}
              />
            ))}
          </TabList>
        </Box>
        {SCENARIOS.map((type) => (
          <TabPanel key={type} value={type} sx={{ px: 1, height: 1, overflow: "auto" }}>
            <UsePromiseCond
              response={config}
              ifFulfilled={(data) => <EnhancedTable type={type} config={data} />}
              ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
            />
          </TabPanel>
        ))}
      </TabContext>
    </BasicDialog>
  );
}

export default ScenarioBuilderDialog;
