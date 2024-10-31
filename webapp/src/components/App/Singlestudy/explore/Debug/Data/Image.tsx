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

import { useTranslation } from "react-i18next";

import ImageIcon from "@mui/icons-material/Image";

import EmptyView from "@/components/common/page/SimpleContent";

import { DataCompProps } from "../utils";

import { Filename, Flex, Menubar } from "./styles";

function Image({ filename }: DataCompProps) {
  const { t } = useTranslation();

  return (
    <Flex>
      <Menubar>
        <Filename>{filename}</Filename>
      </Menubar>
      <EmptyView icon={ImageIcon} title={t("study.debug.file.image")} />
    </Flex>
  );
}

export default Image;
