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

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Button,
  Divider,
  Grid2 as Grid,
  Stack,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import * as R from "ramda";
import type * as RA from "ramda-adjunct";
import { useState } from "react";
import type { StudyMetadata } from "@/types/types";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import type { SubmitHandlerPlus, UseFormReturnPlus } from "@/components/common/Form/types";
import SearchFE from "../../../../../../../common/fieldEditors/SearchFE";
import { isSearchMatching } from "@/utils/stringUtils";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import {
  THEMATIC_TRIMMING_GROUPS,
  getFieldLabelsForGroup,
  type ThematicTrimmingGroup,
} from "./utils";
import type { ThematicTrimmingConfig } from "@/services/api/studies/config/thematicTrimming/types";
import {
  getThematicTrimmingConfig,
  setThematicTrimmingConfig,
} from "@/services/api/studies/config/thematicTrimming";
import { useTranslation } from "react-i18next";

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
      (acc, group) => ({ ...acc, [group]: true }),
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
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdateConfig =
    (api: UseFormReturnPlus<ThematicTrimmingConfig>, fn: RA.Pred) => () => {
      R.toPairs(api.getValues())
        .filter(Boolean)
        .forEach(([key, val]) => {
          api.setValue(key, fn(val));
        });
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
      PaperProps={{
        // TODO: add `maxHeight` and `fullHeight` in BasicDialog`
        sx: { height: "calc(100% - 64px)", maxHeight: "900px" },
      }}
      sx={{
        ".Form": {
          display: "flex",
          flexDirection: "column",
          overflow: "auto",
        },
      }}
      maxWidth="md"
      fullWidth
    >
      {(api) => (
        <>
          <Stack direction="row" justifyContent="space-between" sx={{ pb: 2 }}>
            <SearchFE
              sx={{ m: 0 }}
              value={search}
              onSearchValueChange={setSearch}
              onClear={() => setSearch("")}
            />
            <Stack direction="row" spacing={1}>
              <Button {...commonBtnProps} onClick={handleUpdateConfig(api, R.T)}>
                {t("study.configuration.general.thematicTrimming.action.enableAll")}
              </Button>
              <Button {...commonBtnProps} onClick={handleUpdateConfig(api, R.F)}>
                {t("study.configuration.general.thematicTrimming.action.disableAll")}
              </Button>
              <Button {...commonBtnProps} onClick={handleUpdateConfig(api, R.not)}>
                {t("study.configuration.general.thematicTrimming.action.reverse")}
              </Button>
              <Divider orientation="vertical" flexItem />
              <Button {...commonBtnProps} onClick={() => setExpanded({})}>
                {t("study.configuration.general.thematicTrimming.action.collapseAll")}
              </Button>
            </Stack>
          </Stack>
          {THEMATIC_TRIMMING_GROUPS.map((group) => {
            const fields = getFieldLabelsForGroup(api.getValues(), group)
              .filter(([, label]) => isSearchMatching(search, label))
              .map(([name, label]) => (
                <Grid key={name} size={{ xs: 4 }}>
                  <SwitchFE name={name} label={label} control={api.control} />
                </Grid>
              ));

            return fields.length > 0 ? (
              <Accordion
                key={group}
                expanded={expanded[group] || !!search}
                onChange={(event, isExpanded) => {
                  setExpanded((prev) => ({ ...prev, [group]: isExpanded }));
                }}
                disableGutters
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  {t(`study.configuration.general.thematicTrimming.group.${group}`)}
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={1} sx={{ overflow: "auto", p: 1 }}>
                    {fields}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ) : null;
          })}
        </>
      )}
    </FormDialog>
  );
}

export default ThematicTrimmingDialog;
