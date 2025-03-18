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
import type { LinkElement } from "../../../../../../../types/types";
import { setCurrentArea, setCurrentLink } from "../../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";

import {
  AreaLinkContainer,
  AreaLinkContent,
  AreaLinkRoot,
  AreaLinkTitle,
  AreaLinkLabel,
} from "./style";

interface Props {
  currentLink: LinkElement;
}

function AreaLink({ currentLink }: Props) {
  const [t] = useTranslation();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkClick = (link: string) => {
    dispatch(setCurrentLink(""));
    dispatch(setCurrentArea(link));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <AreaLinkRoot>
      <AreaLinkTitle>{t("study.links")}</AreaLinkTitle>
      <AreaLinkContainer>
        <AreaLinkLabel>{t("study.area1")}</AreaLinkLabel>
        <AreaLinkContent onClick={() => handleLinkClick(currentLink?.area1)}>
          {currentLink?.area1}
        </AreaLinkContent>
      </AreaLinkContainer>
      <AreaLinkContainer>
        <AreaLinkLabel>{t("study.area2")}</AreaLinkLabel>
        <AreaLinkContent onClick={() => handleLinkClick(currentLink?.area2)}>
          {currentLink?.area2}
        </AreaLinkContent>
      </AreaLinkContainer>
    </AreaLinkRoot>
  );
}

export default AreaLink;
