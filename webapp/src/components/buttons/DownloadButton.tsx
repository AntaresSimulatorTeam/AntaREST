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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import type { PromiseAny } from "@/utils/tsUtils";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import { Button } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import SplitButton from "./SplitButton";
import type { Options } from "../utils/buttonOptions";

export type DownloadButtonProps<OptionValue extends string> = {
  children?: React.ReactNode;
  disabled?: boolean;
} & (
  | {
      options: Options<OptionValue>;
      onClick?: (value: OptionValue) => PromiseAny | unknown;
    }
  | {
      options?: undefined;
      onClick?: (value?: undefined) => PromiseAny | unknown;
    }
);

function DownloadButton<OptionValue extends string>(props: DownloadButtonProps<OptionValue>) {
  const { t } = useTranslation();
  const { disabled, options, onClick, children: label = t("global.export") } = props;
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

  const handleDownload = async (value?: OptionValue) => {
    setIsDownloading(true);

    try {
      if (options) {
        if (!value) {
          throw new Error("No value selected");
        }
        await onClick?.(value);
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

  return options ? (
    <SplitButton
      {...btnProps}
      options={options}
      onClick={handleDownload}
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
