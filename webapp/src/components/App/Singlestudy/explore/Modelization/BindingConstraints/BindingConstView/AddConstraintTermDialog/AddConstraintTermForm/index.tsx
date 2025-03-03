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

import { useState } from "react";
import { Box, Button, Typography } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import { useTranslation } from "react-i18next";
import type { AllClustersAndLinks } from "../../../../../../../../../types/types";
import OptionsList from "./OptionsList";
import NumberFE from "../../../../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../../../../common/Form";
import { type ConstraintTerm } from "../../utils";
import ConstraintElement from "../../constraintviews/ConstraintElement";
import OffsetInput from "../../constraintviews/OffsetInput";

interface Props {
  options: AllClustersAndLinks;
  constraintTerms: ConstraintTerm[];
}

export default function AddConstraintTermForm({ options, constraintTerms }: Props) {
  const { control, setValue } = useFormContextPlus<ConstraintTerm>();

  const [t] = useTranslation();
  const [isLink, setIsLink] = useState(true);
  const [isOffset, setIsOffset] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleOffsetRemove = () => {
    setValue("offset", undefined);
    setIsOffset(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        p: 1,
        display: "flex",
        alignItems: "center",
      }}
    >
      <ConstraintElement
        isLink={isLink}
        onToggleType={() => setIsLink((value) => !value)}
        left={
          <NumberFE
            name="weight"
            label={t("study.modelization.bindingConst.weight")}
            variant="outlined"
            control={control}
            rules={{
              required: t("form.field.required"),
            }}
            sx={{ width: 200, mr: 0 }}
          />
        }
        right={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <OptionsList isLink={isLink} list={options} constraintTerms={constraintTerms} />
          </Box>
        }
      />
      {isOffset ? (
        <>
          <Typography sx={{ mx: 2 }}>x</Typography>
          <ConstraintElement
            operator="+"
            left={<Typography>t</Typography>}
            right={
              <OffsetInput onRemove={handleOffsetRemove}>
                <NumberFE
                  name="offset"
                  label={t("study.modelization.bindingConst.offset")}
                  variant="outlined"
                  control={control}
                  rules={{
                    required: t("form.field.required"),
                  }}
                  sx={{ width: 150 }}
                />
              </OffsetInput>
            }
          />
        </>
      ) : (
        <Button
          variant="outlined"
          color="secondary"
          startIcon={<AddCircleOutlineRoundedIcon />}
          sx={{ ml: 3.5 }}
          onClick={() => setIsOffset(true)}
        >
          {t("study.modelization.bindingConst.offset")}
        </Button>
      )}
    </Box>
  );
}
