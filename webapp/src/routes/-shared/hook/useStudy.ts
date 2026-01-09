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

import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudy } from "@/redux/selectors";
import { useParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

function useStudy() {
  const { studyId } = useParams({ strict: false });
  const study = useAppSelector((state) => (studyId ? getStudy(state, studyId) : undefined));
  const { t } = useTranslation();

  if (!studyId) {
    throw new Error(t("route.noParameter", { param: "studyId" }));
  }

  if (!study) {
    throw new Error(t("study.notFound", { id: studyId }));
  }

  return study;
}

export default useStudy;
