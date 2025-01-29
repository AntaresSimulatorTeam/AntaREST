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
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../types/types";
import TabWrapper from "../TabWrapper";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getAreas, getCurrentAreaId, getLinks } from "../../../../../redux/selectors";
import useAppDispatch from "../../../../../redux/hooks/useAppDispatch";
import { setCurrentArea } from "../../../../../redux/ducks/studySyntheses";

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

    return [
      {
        label: t("study.modelization.map"),
        path: `${basePath}/map`,
      },
      {
        label: t("study.areas"),
        path: `${basePath}/area/${encodeURI(areaId)}`,
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

  return (
    <Box
      sx={{
        display: "flex",
        flex: 1,
        width: 1,
        overflow: "hidden",
      }}
    >
      <TabWrapper study={study} tabStyle="withoutBorder" tabList={tabList} />
    </Box>
  );
}

export default Modelization;
