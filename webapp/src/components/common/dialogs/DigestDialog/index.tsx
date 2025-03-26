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

import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import client from "@/services/api/client";
import { Skeleton } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { LaunchJob } from "../../../../types/types";
import UsePromiseCond from "../../utils/UsePromiseCond";
import OkDialog, { type OkDialogProps } from "../OkDialog";
import DigestTabs from "./DigestTabs";
import type { DigestData } from "./types";

interface DigestDialogProps extends Pick<OkDialogProps, "open" | "onOk" | "onClose"> {
  studyId: LaunchJob["studyId"];
  outputId: LaunchJob["outputId"];
}

function DigestDialog({ studyId, outputId, ...dialogProps }: DigestDialogProps) {
  const { t } = useTranslation();

  const digestRes = usePromiseWithSnackbarError(
    () => client.get<DigestData>(`/v1/private/studies/${studyId}/outputs/${outputId}/digest-ui`),
    {
      errorMessage: t("data.error.matrix"),
      deps: [studyId, outputId],
    },
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <OkDialog
      {...dialogProps}
      title="Digest"
      okButtonText={t("global.close")}
      fullScreen
      sx={{ m: 5 }}
    >
      <UsePromiseCond
        response={digestRes}
        ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
        ifFulfilled={(matrices) => <DigestTabs matrices={matrices.data} />}
      />
    </OkDialog>
  );
}

export default DigestDialog;
