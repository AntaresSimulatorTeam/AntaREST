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

import { useRef } from "react";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";
import { Box, ButtonBase } from "@mui/material";

interface PropTypes {
  onImport: (json: object) => void;
}

function CommandImportButton(props: PropTypes) {
  const { onImport } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onButtonClick = () => {
    if (inputRef.current) {
      inputRef.current.click();
    }
  };

  const onInputClick = (e: React.MouseEvent<HTMLInputElement | MouseEvent>) => {
    if (e && e.target) {
      const element = e.target as HTMLInputElement;
      element.value = "";
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    const reader = new FileReader();
    reader.onload = async (ev: ProgressEvent<FileReader>) => {
      try {
        if (ev.target) {
          const text = ev.target.result;
          const json = JSON.parse(text as string);
          onImport(json);
        }
      } catch (error) {
        enqueueSnackbar(t("variants.error.jsonParsing"), {
          variant: "error",
        });
      }
    };
    if (e.target && e.target.files) {
      reader.readAsText(e.target.files[0]);
    }
  };

  return (
    <Box display="flex" alignItems="center">
      <ButtonBase
        type="submit"
        sx={{ width: "auto", height: "auto" }}
        onClick={onButtonClick}
      >
        <CloudUploadOutlinedIcon
          sx={{
            width: "24px",
            height: "auto",
            cursor: "pointer",
            color: "primary.main",
            mx: 0.5,
            "&:hover": {
              color: "primary.dark",
            },
          }}
        />
      </ButtonBase>
      <input
        style={{ display: "none" }}
        type="file"
        name="file"
        accept="application/json"
        onChange={(e) => handleChange(e)}
        onClick={(e) => onInputClick(e)}
        ref={(e) => {
          inputRef.current = e;
        }}
      />
    </Box>
  );
}

export default CommandImportButton;
