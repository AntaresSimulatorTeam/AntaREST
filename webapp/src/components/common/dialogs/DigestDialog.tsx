/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Skeleton } from "@mui/material";
import OkDialog, { OkDialogProps } from "./OkDialog";
import UsePromiseCond from "../utils/UsePromiseCond";
import type { LaunchJob } from "../../../common/types";
import { getStudyData } from "../../../services/api/study";
import usePromise from "../../../hooks/usePromise";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import EmptyView from "../page/SimpleContent";
import SearchOffIcon from "@mui/icons-material/SearchOff";
import MatrixGrid from "@/components/common/Matrix/components/MatrixGrid";
import { generateDataColumns } from "@/components/common/Matrix/shared/utils";

export interface DigestDialogProps
  extends Pick<OkDialogProps, "open" | "onOk" | "onClose"> {
  studyId: LaunchJob["studyId"];
  outputId: LaunchJob["outputId"];
}

function DigestDialog({
  studyId,
  outputId,
  ...dialogProps
}: DigestDialogProps) {
  const { t } = useTranslation();

  const synthesisRes = usePromise(
    () =>
      getStudyData(studyId, `output/${outputId}/economy/mc-all/grid/digest`),
    {
      deps: [studyId, outputId],
    },
  );

  console.log("synthesisRes", synthesisRes);

  return (
    <OkDialog
      {...dialogProps}
      title="Digest"
      okButtonText={t("global.close")}
      fullScreen
      sx={{ m: 5 }}
    >
      <UsePromiseCond
        response={synthesisRes}
        ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
        ifRejected={(error) => {
          if (error instanceof AxiosError && error.response?.status === 404) {
            return (
              <EmptyView
                title={t("global.error.fileNotFound")}
                icon={SearchOffIcon}
              />
            );
          }
          return <EmptyView title={error?.toString()} />;
        }}
        ifFulfilled={(matrix) =>
          matrix && (
            <MatrixGridSynthesis
              data={matrix.data}
              rows={matrix.length}
              columns={generateDataColumns(true, matrix.columns.length)}
              readOnly
            />
          )
        }
      />
    </OkDialog>
  );
}

export default DigestDialog;
