/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import SearchFE from "@/components/fieldEditors/SearchFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import {
  getThematicTrimmingConfig,
  setThematicTrimmingConfig,
} from "@/services/api/studies/config/thematicTrimming";
import type { ThematicTrimmingConfig } from "@/services/api/studies/config/thematicTrimming/types";
import type { StudyMetadata } from "@/types/types";
import { isSearchMatching } from "@/utils/stringUtils";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  ButtonGroup,
  Grid2 as Grid,
  Stack,
  Typography,
} from "@mui/material";
import * as R from "ramda";
import type * as RA from "ramda-adjunct";
import { useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { useTranslation } from "react-i18next";
import {
  THEMATIC_TRIMMING_GROUPS,
  getFieldLabelsForGroup,
  getValuesForGroup,
  type ThematicTrimmingGroup,
} from "./utils";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

function ThematicTrimmingDialog(props: Props) {
  const { study, open, onClose } = props;
  const { t } = useTranslation();
  const [search, setSearch] = useState("");

  const [expanded, setExpanded] = useState(() =>
    THEMATIC_TRIMMING_GROUPS.reduce(
      (acc, group) => {
        acc[group] = true;
        return acc;
      },
      {} as Partial<Record<ThematicTrimmingGroup, boolean>>,
    ),
  );

  const commonBtnProps = {
    color: "secondary",
    // Disable all buttons when search is active to remove confusion
    // about which fields are being affected by the action (search or all)
    disabled: !!search,
  } as const;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const setGroupExpanded = (group: ThematicTrimmingGroup, isExpanded: boolean) => {
    setExpanded((prev) => ({ ...prev, [group]: isExpanded }));
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdateConfig =
    (fn: RA.Pred, formApi: UseFormReturn<ThematicTrimmingConfig>, group?: ThematicTrimmingGroup) =>
    (event: React.MouseEvent<HTMLButtonElement>) => {
      R.toPairs(group ? getValuesForGroup(formApi.getValues(), group) : formApi.getValues())
        .filter(Boolean)
        .forEach(([key, val]) => {
          formApi.setValue(key, fn(val), { shouldDirty: true });
        });

      if (group) {
        // Prevent accordion collapse when clicking the buttons
        event.stopPropagation();

        if (!expanded[group]) {
          setGroupExpanded(group, true);
        }
      }
    };

  const handleSubmit = (data: SubmitHandlerPlus<ThematicTrimmingConfig>) => {
    return setThematicTrimmingConfig({
      studyId: study.id,
      config: data.values,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      key={study.id}
      open={open}
      title="Thematic Trimming"
      config={{
        defaultValues: () => getThematicTrimmingConfig({ studyId: study.id }),
      }}
      onSubmit={handleSubmit}
      onCancel={onClose}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: { height: 1 },
        },
      }}
    >
      {(formApi) => (
        <Stack spacing={2} direction="column" sx={{ height: 1 }}>
          <Stack justifyContent="space-between">
            <SearchFE
              sx={{ m: 0 }}
              value={search}
              onSearchValueChange={setSearch}
              size="extra-small"
            />
            <ButtonGroup color="secondary">
              <Button {...commonBtnProps} onClick={handleUpdateConfig(R.T, formApi)}>
                {t("study.configuration.general.thematicTrimming.action.enableAll")}
              </Button>
              <Button {...commonBtnProps} onClick={handleUpdateConfig(R.F, formApi)}>
                {t("study.configuration.general.thematicTrimming.action.disableAll")}
              </Button>
              <Button {...commonBtnProps} onClick={handleUpdateConfig(R.not, formApi)}>
                {t("global.reverse")}
              </Button>
              <Button {...commonBtnProps} onClick={() => setExpanded({})}>
                {t("study.configuration.general.thematicTrimming.action.collapseAll")}
              </Button>
            </ButtonGroup>
          </Stack>

          <Box sx={{ overflow: "auto" }}>
            {THEMATIC_TRIMMING_GROUPS.map((group) => {
              const fields = getFieldLabelsForGroup(formApi.getValues(), group)
                .filter(([, label]) => isSearchMatching(search, label))
                .map(([name, label]) => (
                  <Grid key={name} size={{ xs: 4 }}>
                    <SwitchFE name={name} label={label} control={formApi.control} />
                  </Grid>
                ));

              return fields.length > 0 ? (
                <Accordion
                  key={group}
                  expanded={expanded[group] || !!search}
                  onChange={(_, isExpanded) => setGroupExpanded(group, isExpanded)}
                  disableGutters
                >
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography sx={{ flex: 1 }}>
                      {t(`study.configuration.general.thematicTrimming.group.${group}`)}
                    </Typography>
                    <ButtonGroup variant="text" color="secondary" size="extra-small" sx={{ mr: 2 }}>
                      <Button {...commonBtnProps} onClick={handleUpdateConfig(R.T, formApi, group)}>
                        {t("study.configuration.general.thematicTrimming.action.enableAll")}
                      </Button>
                      <Button {...commonBtnProps} onClick={handleUpdateConfig(R.F, formApi, group)}>
                        {t("study.configuration.general.thematicTrimming.action.disableAll")}
                      </Button>
                      <Button
                        {...commonBtnProps}
                        onClick={handleUpdateConfig(R.not, formApi, group)}
                      >
                        {t("global.reverse")}
                      </Button>
                    </ButtonGroup>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={1} sx={{ overflow: "auto", p: 1 }}>
                      {fields}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              ) : null;
            })}
          </Box>
        </Stack>
      )}
    </FormDialog>
  );
}

export default ThematicTrimmingDialog;
