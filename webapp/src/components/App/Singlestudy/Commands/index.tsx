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
import { Toolbar, Divider, Typography } from "@mui/material";
import { CommandDrawer, TitleContainer } from "./style";
import EditionView from "./Edition";

interface Props {
  open: boolean;
  onClose: () => void;
  studyId: string;
}

function CommandsDrawer(props: Props) {
  const [t] = useTranslation();
  const { open, onClose, studyId } = props;

  return (
    <CommandDrawer variant="temporary" anchor="right" open={open} onClose={onClose}>
      <Toolbar sx={{ py: 3 }}>
        <TitleContainer>
          <Typography sx={{ color: "grey.500", fontSize: "0.9em" }}>
            {t("variants.commands").toUpperCase()}
          </Typography>
        </TitleContainer>
      </Toolbar>
      <Divider style={{ height: "1px" }} />
      <EditionView studyId={studyId} />
    </CommandDrawer>
  );
}

export default CommandsDrawer;
