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
import type { StudyMetadata } from "../../../../../../../types/types";
import type { BindingConstraint } from "./utils";
import SplitView from "../../../../../../common/SplitView";
import { Box, Button } from "@mui/material";
import BasicDialog, { type BasicDialogProps } from "../../../../../../common/dialogs/BasicDialog";
import Matrix from "../../../../../../common/Matrix";
import { useFormContextPlus } from "@/components/common/Form";

interface Props {
  study: StudyMetadata;
  constraintId: string;
  open: boolean;
  onClose: () => void;
}

function ConstraintMatrix({ study, constraintId, open, onClose }: Props) {
  const { getValues } = useFormContextPlus<BindingConstraint>();
  const operator = getValues("operator");

  const { t } = useTranslation();
  const dialogProps: BasicDialogProps = {
    open,
    onClose,
    actions: (
      <Button onClick={onClose} color="primary" variant="outlined">
        {t("global.close")}
      </Button>
    ),
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      contentProps={{
        sx: { p: 1, height: "95vh" },
      }}
      fullWidth
      maxWidth="xl"
      {...dialogProps}
    >
      {Number(study.version) >= 870 ? (
        <>
          {operator === "less" && (
            <Matrix
              title={t("study.modelization.bindingConst.timeSeries.less")}
              url={`input/bindingconstraints/${constraintId}_lt`}
            />
          )}
          {operator === "equal" && (
            <Matrix
              title={t("study.modelization.bindingConst.timeSeries.equal")}
              url={`input/bindingconstraints/${constraintId}_eq`}
            />
          )}
          {operator === "greater" && (
            <Matrix
              title={t("study.modelization.bindingConst.timeSeries.greater")}
              url={`input/bindingconstraints/${constraintId}_gt`}
            />
          )}
          {operator === "both" && (
            <SplitView splitId="binding-constraints-matrix" sizes={[50, 50]}>
              <Box sx={{ px: 2 }}>
                <Matrix
                  title={t("study.modelization.bindingConst.timeSeries.less")}
                  url={`input/bindingconstraints/${constraintId}_lt`}
                />
              </Box>
              <Box sx={{ px: 2 }}>
                <Matrix
                  title={t("study.modelization.bindingConst.timeSeries.greater")}
                  url={`input/bindingconstraints/${constraintId}_gt`}
                />
              </Box>
            </SplitView>
          )}
        </>
      ) : (
        <Matrix
          title={t("global.matrix")}
          url={`input/bindingconstraints/${constraintId}`}
          customColumns={["<", ">", "="]}
        />
      )}
    </BasicDialog>
  );
}

export default ConstraintMatrix;
