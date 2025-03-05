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

import { useMemo, useState } from "react";
import { Button, ButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import * as R from "ramda";
import type { XpansionCandidate } from "../types";
import FormDialog from "../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import Fieldset from "../../../../../common/Fieldset";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import type { SubmitHandlerPlus } from "../../../../../common/Form/types";
import { validateString } from "@/utils/validation/string";
import type { LinkDTO } from "@/services/api/studies/links/types";

interface PropType {
  open: boolean;
  links: LinkDTO[];
  onClose: () => void;
  onSave: (candidate: XpansionCandidate) => void;
  candidates: XpansionCandidate[];
}

function CreateCandidateDialog(props: PropType) {
  const { open, links, onClose, onSave, candidates } = props;
  const [t] = useTranslation();
  const [isToggled, setIsToggled] = useState(true);

  const existingCandidates = useMemo(() => candidates.map(({ name }) => name), [candidates]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleToggle = () => {
    setIsToggled(!isToggled);
  };

  const handleSubmit = (data: SubmitHandlerPlus<XpansionCandidate>) => {
    const values = R.omit(isToggled ? ["max-investment"] : ["unit-size", "max-units"], data.values);

    onSave(values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      onCancel={onClose}
      title={t("xpansion.newCandidate")}
      titleIcon={AddCircleIcon}
      onSubmit={handleSubmit}
      config={{
        defaultValues: {
          name: "",
          link: "",
          "annual-cost-per-mw": 0,
          "unit-size": 0,
          "max-units": 0,
          "max-investment": 0,
        },
      }}
    >
      {({ control }) => (
        <>
          <Fieldset fullFieldWidth>
            <StringFE
              label={t("global.name")}
              name="name"
              control={control}
              rules={{
                validate: (v) =>
                  validateString(v, {
                    existingValues: existingCandidates,
                    allowSpaces: false,
                    specialChars: "&_*",
                  }),
              }}
              sx={{ mx: 0 }}
            />
            <SelectFE
              label={t("xpansion.link")}
              options={links.map((link) => `${link.area1} - ${link.area2}`)}
              name="link"
              control={control}
              rules={{ required: t("form.field.required") }}
              fullWidth
            />
            <NumberFE
              label={t("xpansion.annualCost")}
              name="annual-cost-per-mw"
              control={control}
              rules={{
                min: {
                  value: 1,
                  message: t("form.field.minValue", { 0: 1 }),
                },
              }}
              sx={{ mx: 0 }}
            />
          </Fieldset>

          <Fieldset
            fullFieldWidth
            legend={
              isToggled
                ? `${t("xpansion.unitSize")} & ${t("xpansion.maxUnits")}`
                : t("xpansion.maxInvestments")
            }
          >
            <ButtonGroup disableElevation color="info" sx={{ py: 2 }}>
              <Button onClick={handleToggle} variant={!isToggled ? "outlined" : "contained"}>
                {`${t("xpansion.unitSize")} & ${t("xpansion.maxUnits")}`}
              </Button>
              <Button onClick={handleToggle} variant={isToggled ? "outlined" : "contained"}>
                {t("xpansion.maxInvestments")}
              </Button>
            </ButtonGroup>
            {isToggled ? (
              <>
                <NumberFE
                  label={t("xpansion.unitSize")}
                  name="unit-size"
                  control={control}
                  sx={{ mx: 0 }}
                />
                <NumberFE
                  label={t("xpansion.maxUnits")}
                  name="max-units"
                  control={control}
                  sx={{ mx: 0 }}
                />
              </>
            ) : (
              <NumberFE
                label={t("xpansion.maxInvestments")}
                name="max-investment"
                control={control}
                sx={{ mx: 0 }}
              />
            )}
          </Fieldset>
        </>
      )}
    </FormDialog>
  );
}

export default CreateCandidateDialog;
