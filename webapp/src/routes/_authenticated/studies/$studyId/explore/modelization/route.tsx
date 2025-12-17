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

import TabsView from "@/components/page/TabsView";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/modelization")({
  component: ModelizationLayout,
});

function ModelizationLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();
  // const dispatch = useAppDispatch();
  // const navigate = useNavigate();
  // const { areaId: paramAreaId } = useParams();
  // const areas = useAppSelector((state) => getAreas(state, study.id));
  // const links = useAppSelector((state) => getLinks(state, study.id));
  // const areaId = useAppSelector(getCurrentAreaId);

  // useEffect(() => {
  //   if (!areaId && paramAreaId) {
  //     dispatch(setCurrentArea(paramAreaId));
  //   }
  // }, [paramAreaId, dispatch, areaId]);

  // const tabList = useMemo(() => {
  // const basePath = `/studies/${study.id}/explore/modelization`;

  // const handleAreasClick = () => {
  //   if (areaId.length === 0 && areas.length > 0) {
  //     const firstAreaId = areas[0].id ?? null;

  //     if (firstAreaId) {
  //       dispatch(setCurrentArea(firstAreaId));
  //       navigate(`${basePath}/area/${firstAreaId}`, {
  //         replace: true,
  //       });
  //     }
  //   }
  // };

  // const areaPath = [basePath, "area", encodeURI(areaId || areas[0]?.id || "")].join("/");

  // }, [areaId, areas, dispatch, links, navigate, study.id, t]);

  return (
    <TabsView
      tabs={[
        {
          id: "map",
          label: t("study.modelization.map"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modelization/map",
            params,
          }),
        },
        {
          id: "areas",
          label: t("study.areas"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modelization/areas",
            params,
          }),
          // path: areaPath,
          // onClick: handleAreasClick,
          // disabled: areas.length === 0,
        },
        // {
        //   label: t("study.links"),
        //   path: `${basePath}/links`,
        //   disabled: links.length === 0,
        // },
        // {
        //   label: t("study.bindingConstraints"),
        //   path: `${basePath}/bindingcontraint`,
        // },
      ]}
      divider
    />
  );
}
