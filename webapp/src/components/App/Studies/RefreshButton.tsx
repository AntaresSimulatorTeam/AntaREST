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

import { Button, Tooltip } from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useTranslation } from "react-i18next";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { fetchStudies } from "../../../redux/ducks/studies";

interface Props {
  showLabel?: boolean;
}

function RefreshButton(props: Props) {
  const { showLabel } = props;
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  const buttonProps = {
    endIcon: showLabel ? <RefreshIcon /> : undefined,
    children: showLabel ? t("studies.refresh") : <RefreshIcon />,
  };

  return (
    <Tooltip title={t("studies.refresh") as string} sx={{ mr: 4 }}>
      <Button
        color="primary"
        onClick={() => dispatch(fetchStudies())}
        variant="outlined"
        {...buttonProps}
      />
    </Tooltip>
  );
}

export default RefreshButton;
