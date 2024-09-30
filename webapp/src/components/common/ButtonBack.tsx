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

import { Box, Button } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";

interface Props {
  onClick: VoidFunction;
}

function ButtonBack(props: Props) {
  const { onClick } = props;
  const [t] = useTranslation();

  return (
    <Box
      width="100%"
      display="flex"
      flexDirection="row"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
    >
      <Button
        startIcon={<ArrowBackIcon />}
        variant="text"
        color="secondary"
        onClick={() => onClick()}
      >
        {t("button.back")}
      </Button>
    </Box>
  );
}

export default ButtonBack;
