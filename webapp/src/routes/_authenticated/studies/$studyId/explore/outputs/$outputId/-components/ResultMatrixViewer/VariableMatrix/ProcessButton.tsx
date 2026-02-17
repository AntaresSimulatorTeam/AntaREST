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

import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { Button, CircularProgress } from "@mui/material";
import { useTranslation } from "react-i18next";

interface ProcessButtonProps {
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
}

function ProcessButton({ onClick, loading = false, disabled = false }: ProcessButtonProps) {
  const { t } = useTranslation();

  return (
    <Button
      variant="contained"
      color="primary"
      onClick={onClick}
      disabled={disabled || loading}
      startIcon={loading ? <CircularProgress size={16} /> : <PlayArrowIcon />}
    >
      {t("study.outputs.process")}
    </Button>
  );
}

export default ProcessButton;
