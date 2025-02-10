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
import { Box, Typography } from "@mui/material";
import { Code } from "./styles";
import OkDialog from "../OkDialog";
import SimpleLoader from "../../loaders/SimpleLoader";
import MatrixGrid from "@/components/common/Matrix/components/MatrixGrid";
import { generateDataColumns } from "@/components/common/Matrix/shared/utils";
import type { MatrixDataDTO } from "@/components/common/Matrix/shared/types";

interface Props {
  filename: string;
  content?: string | MatrixDataDTO;
  loading?: boolean;
  onClose: () => void;
  isMatrix?: boolean;
}

function isMatrixData(content: string | MatrixDataDTO): content is MatrixDataDTO {
  return typeof content === "object" && "data" in content && "columns" in content;
}

/**
 * @deprecated This component is legacy and only used in Xpansion views.
 * TODO: This component should be removed when the Xpansion views are reworked.
 * The new implementation should separate the following responsibilities:
 * - Matrix data visualization
 * - Text content display
 *
 * @param props - Component props
 * @param props.filename - The name of the file to be displayed
 * @param [props.content] - The content to be displayed, either text or matrix data
 * @param props.onClose - Callback function to handle dialog close
 * @param [props.isMatrix] - Flag indicating if the content is matrix data
 * @param [props.loading] - Flag indicating if the content is being loaded
 * @returns The rendered DataViewerDialog component
 */
function DataViewerDialog({ filename, content, onClose, isMatrix, loading }: Props) {
  const [t] = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <OkDialog
      open
      title={
        isMatrix && content && isMatrixData(content) ? (
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography
              sx={{ fontWeight: 500, fontSize: "1.25rem" }}
            >{`Matrix - ${filename}`}</Typography>
          </Box>
        ) : (
          filename
        )
      }
      contentProps={{
        sx: { p: 0, height: "60vh", overflow: "hidden" },
      }}
      fullWidth
      maxWidth="lg"
      okButtonText={t("global.close")}
      onOk={onClose}
    >
      {loading && !content && <SimpleLoader />}
      {content && (
        <>
          {isMatrix && isMatrixData(content) && (
            <MatrixGrid
              data={content.data}
              rows={content.data.length}
              columns={generateDataColumns({
                isTimeSeries: true,
                count: content.columns.length,
              })}
              readOnly
            />
          )}
          {!isMatrix && typeof content === "string" && (
            <Code>
              <code style={{ whiteSpace: "pre" }}>{content}</code>
            </Code>
          )}
        </>
      )}
    </OkDialog>
  );
}

export default DataViewerDialog;
