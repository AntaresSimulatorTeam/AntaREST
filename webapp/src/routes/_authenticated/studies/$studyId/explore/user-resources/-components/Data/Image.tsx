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

import DownloadButton from "@/components/buttons/DownloadButton";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getUserResourceContent } from "@/services/api/studies/userResources";
import { downloadFile } from "@/utils/fileUtils";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useUnmount } from "react-use";
import type { DataCompProps } from "../../-utils";
import { Filename, Menubar } from "./styles";

function Image({ studyId, path, name, type }: DataCompProps) {
  const { t } = useTranslation();

  const imageResponse = usePromiseWithSnackbarError(
    async () => {
      const imageBlob = await getUserResourceContent({ studyId, path });
      const imageUrl = URL.createObjectURL(imageBlob);
      return { imageBlob, imageUrl };
    },
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, path, type],
    },
  );

  useUnmount(() => {
    if (imageResponse.data) {
      URL.revokeObjectURL(imageResponse.data.imageUrl);
    }
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={imageResponse}
      ifFulfilled={({ imageBlob, imageUrl }) => (
        <>
          <Menubar>
            <Filename>{name}</Filename>
            <DownloadButton onClick={() => downloadFile(imageBlob, name)} />
          </Menubar>
          <Box
            component="img"
            src={imageUrl}
            alt={name}
            sx={{
              objectFit: "contain",
              overflow: "auto",
            }}
          />
        </>
      )}
    />
  );
}

export default Image;
