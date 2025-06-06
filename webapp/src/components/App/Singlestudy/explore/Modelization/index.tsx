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

import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import { setCurrentArea } from "../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getAreas, getCurrentAreaId, getLinks } from "../../../../../redux/selectors";
import type { StudyMetadata } from "../../../../../types/types";
import TabWrapper from "../TabWrapper";

function Modelization() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { areaId: paramAreaId } = useParams();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const links = useAppSelector((state) => getLinks(state, study.id));
  const areaId = useAppSelector(getCurrentAreaId);

  useEffect(() => {
    if (!areaId && paramAreaId) {
      dispatch(setCurrentArea(paramAreaId));
    }
  }, [paramAreaId, dispatch, areaId]);

  const tabList = useMemo(() => {
    const basePath = `/studies/${study.id}/explore/modelization`;

    const handleAreasClick = () => {
      if (areaId.length === 0 && areas.length > 0) {
        const firstAreaId = areas[0].id ?? null;

        if (firstAreaId) {
          dispatch(setCurrentArea(firstAreaId));
          navigate(`${basePath}/area/${firstAreaId}`, {
            replace: true,
          });
        }
      }
    };

    const areaPath = [basePath, "area", encodeURI(areaId || areas[0]?.id || "")].join("/");

    return [
      {
        label: t("study.modelization.map"),
        path: `${basePath}/map`,
      },
      {
        label: t("study.areas"),
        path: areaPath,
        onClick: handleAreasClick,
        disabled: areas.length === 0,
      },
      {
        label: t("study.links"),
        path: `${basePath}/links`,
        disabled: links.length === 0,
      },
      {
        label: t("study.bindingConstraints"),
        path: `${basePath}/bindingcontraint`,
      },
    ];
  }, [areaId, areas, dispatch, links, navigate, study.id, t]);

  return <TabWrapper study={study} tabList={tabList} disablePadding />;
}

export default Modelization;
