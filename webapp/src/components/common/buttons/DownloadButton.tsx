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

import FileDownloadIcon from "@mui/icons-material/FileDownload";
import SplitButton, { type SplitButtonProps } from "./SplitButton";
import { useState } from "react";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { useTranslation } from "react-i18next";
import type { PromiseAny } from "../../../utils/tsUtils";
import { toError } from "../../../utils/fnUtils";
import { Button } from "@mui/material";

export type DownloadButtonProps<OptionValue extends string> = {
  children?: React.ReactNode;
  disabled?: boolean;
} & (
  | {
      formatOptions: SplitButtonProps<OptionValue>["options"];
      onClick?: (format: OptionValue) => PromiseAny | unknown;
    }
  | {
      formatOptions?: undefined;
      onClick?: (format?: undefined) => PromiseAny | unknown;
    }
);

function DownloadButton<OptionValue extends string>(props: DownloadButtonProps<OptionValue>) {
  const { t } = useTranslation();
  const { disabled, formatOptions, onClick, children: label = t("global.export") } = props;
  const [isDownloading, setIsDownloading] = useState(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const btnProps = {
    variant: "contained",
    size: "small",
    disabled,
  } as const;

  const loadingBtnProps = {
    startIcon: <FileDownloadIcon />,
    loadingPosition: "start",
    loading: isDownloading,
  } as const;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format?: OptionValue) => {
    setIsDownloading(true);

    try {
      if (formatOptions) {
        if (!format) {
          throw new Error("No format selected");
        }
        await onClick?.(format);
      } else {
        await onClick?.();
      }
    } catch (err) {
      enqueueErrorSnackbar(t("global.export.error"), toError(err));
    }

    setIsDownloading(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return formatOptions ? (
    <SplitButton
      {...btnProps}
      options={formatOptions}
      onClick={(format) => handleDownload(format)}
      ButtonProps={loadingBtnProps}
    >
      {label}
    </SplitButton>
  ) : (
    <Button {...btnProps} {...loadingBtnProps} onClick={() => handleDownload()}>
      {label}
    </Button>
  );
}

export default DownloadButton;
